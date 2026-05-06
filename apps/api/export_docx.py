"""DOCX export generation for audit reports."""

from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from apps.api.export_data import ExportReportData
from apps.api.export_openxml import join_values, number, percent, xml_text

TableRows = list[list[object]]


def generate_docx_export(data: ExportReportData) -> bytes:
    document = _document_xml(data)
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types())
        archive.writestr("_rels/.rels", _root_rels())
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", _document_rels())
        archive.writestr("word/styles.xml", _styles_xml())
    return buffer.getvalue()


def _document_xml(data: ExportReportData) -> str:
    body_parts = [
        _heading(f"Audit report: {data.audit_metadata.brand_name}", 1),
        _paragraph(f"Audit #{data.audit_id} · {data.audit_metadata.status}"),
        _paragraph(f"Generated at {data.generated_at.isoformat()}"),
        _heading("Audit metadata", 2),
        _table(
            [
                ["Field", "Value"],
                ["Brand domain", data.audit_metadata.brand_domain],
                ["SCDL level", data.audit_metadata.scdl_level],
                ["Providers", join_values(data.audit_metadata.providers)],
                ["Language", data.audit_metadata.language],
                ["Country", data.audit_metadata.country],
                ["Locale", data.audit_metadata.locale],
                ["Queries", data.summary.totals.query_count],
                ["Targets", data.summary.totals.target_count],
                ["Runs", data.summary.totals.run_count],
            ]
        ),
        _heading("General summary", 2),
        _table(
            [
                ["Metric", "Value"],
                ["Mentionability L1", percent(data.summary.overall.mentionability_l1.percentage)],
                ["Mentionability L2", percent(data.summary.overall.mentionability_l2.percentage)],
                ["Accuracy L1", percent(data.summary.overall.accuracy_l1)],
                ["Accuracy L2", percent(data.summary.overall.accuracy_l2)],
                ["Tone positive", data.summary.overall.tone.positive],
                ["Tone neutral", data.summary.overall.tone.neutral],
                ["Tone negative", data.summary.overall.tone.negative],
                ["Tone unknown", data.summary.overall.tone.unknown],
            ]
        ),
        _heading("Model summary", 2),
        _table(_model_summary_rows(data)),
        _heading("Answer matrix summary", 2),
        *_answer_matrix_sections(data),
        _heading("Source domains", 2),
        _table(_source_domain_rows(data)),
        _heading("Concepts", 2),
        _table(_concept_rows(data)),
        _heading("Competitor candidates", 2),
        _table(_competitor_rows(data)),
        _heading("Provider diagnostics", 2),
        _table(_diagnostic_rows(data)),
        _heading("Methodology notes", 2),
        _paragraph("L1 = AI answer without web access. L2 = AI answer with web access."),
        _paragraph("OpenRouter L2 results are experimental when marked by the backend."),
        _paragraph("Raw provider responses, prompts, headers, and secrets are excluded."),
    ]
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>{''.join(body_parts)}<w:sectPr/></w:body>
</w:document>"""


def _model_summary_rows(data: ExportReportData) -> TableRows:
    rows: TableRows = [
        [
            "Model",
            "MR L1",
            "MR L2",
            "Delta MR",
            "Accuracy L1",
            "Accuracy L2",
            "Delta accuracy",
            "Tone L1",
            "Tone L2",
        ]
    ]
    for item in data.summary.model_summaries:
        rows.append(
            [
                item.target_group_label,
                percent(item.mr_l1),
                percent(item.mr_l2),
                number(item.delta_mr),
                percent(item.accuracy_l1),
                percent(item.accuracy_l2),
                number(item.delta_accuracy),
                item.tone_l1,
                item.tone_l2,
            ]
        )
    return rows


def _answer_matrix_sections(data: ExportReportData) -> list[str]:
    columns = {column.target_id: column for column in data.answer_matrix.columns}
    if not data.answer_matrix.rows:
        return [_paragraph("No answer matrix rows available.")]

    sections: list[str] = []
    for row in data.answer_matrix.rows:
        table_rows: TableRows = [["Model/level", "Status", "Verdict", "Answer excerpt"]]
        for cell in row.cells:
            column = columns.get(cell.target_id)
            label = f"{column.label} / {column.level}" if column else cell.target_id
            table_rows.append(
                [
                    label,
                    cell.status,
                    cell.evaluation.verdict if cell.evaluation else "",
                    cell.answer_excerpt,
                ]
            )
        sections.append(_heading(row.query_text, 3))
        sections.append(_table(table_rows))
    return sections


def _source_domain_rows(data: ExportReportData) -> TableRows:
    rows: TableRows = [
        ["Domain", "Sources", "URLs", "Queries", "Targets", "Models", "Providers"]
    ]
    for domain in data.source_domains.domains:
        rows.append(
            [
                domain.domain,
                domain.source_count,
                domain.unique_url_count,
                domain.query_count,
                domain.target_count,
                join_values(domain.models[:5]),
                join_values(domain.providers),
            ]
        )
    if len(rows) == 1:
        rows.append(["No source domains available.", "", "", "", "", "", ""])
    return rows


def _concept_rows(data: ExportReportData) -> TableRows:
    rows: TableRows = [["Concept", "Category", "Count", "Evidence count"]]
    for concept in data.concepts:
        rows.append([concept.text, concept.category, concept.count, concept.evidence_count])
    if len(rows) == 1:
        rows.append(["No concepts available.", "", "", ""])
    return rows


def _competitor_rows(data: ExportReportData) -> TableRows:
    rows: TableRows = [["Name", "Domain", "Confidence", "Evidence type", "Evidence count"]]
    for candidate in data.competitor_candidates:
        rows.append(
            [
                candidate.name,
                candidate.domain,
                number(candidate.confidence),
                candidate.evidence_type,
                candidate.evidence_count,
            ]
        )
    if len(rows) == 1:
        rows.append(["No competitor candidates available.", "", "", "", ""])
    return rows


def _diagnostic_rows(data: ExportReportData) -> TableRows:
    rows: TableRows = [["Code", "Message", "Provider", "Model", "Level", "Retryable"]]
    for diagnostic in data.provider_diagnostics:
        rows.append(
            [
                diagnostic.code,
                diagnostic.message,
                diagnostic.provider,
                diagnostic.model,
                diagnostic.level,
                diagnostic.retryable,
            ]
        )
    if len(rows) == 1:
        rows.append(["No provider diagnostics.", "", "", "", "", ""])
    return rows


def _heading(text: object, level: int) -> str:
    size = {1: "32", 2: "26", 3: "22"}.get(level, "22")
    return (
        "<w:p><w:pPr><w:keepNext/></w:pPr><w:r><w:rPr><w:b/>"
        f'<w:sz w:val="{size}"/></w:rPr><w:t>{xml_text(text)}</w:t></w:r></w:p>'
    )


def _paragraph(text: object) -> str:
    return f"<w:p><w:r><w:t>{xml_text(text)}</w:t></w:r></w:p>"


def _table(rows: TableRows) -> str:
    row_xml = "".join(_table_row(row, bold=index == 0) for index, row in enumerate(rows))
    return f"<w:tbl>{row_xml}</w:tbl>"


def _table_row(row: list[object], *, bold: bool = False) -> str:
    return "<w:tr>" + "".join(_table_cell(value, bold=bold) for value in row) + "</w:tr>"


def _table_cell(value: object, *, bold: bool = False) -> str:
    bold_xml = "<w:b/>" if bold else ""
    return (
        "<w:tc><w:p><w:r><w:rPr>"
        f"{bold_xml}</w:rPr><w:t>{xml_text(value)}</w:t></w:r></w:p></w:tc>"
    )


def _content_types() -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
            (
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-'
                'package.relationships+xml"/>'
            ),
            '<Default Extension="xml" ContentType="application/xml"/>',
            (
                '<Override PartName="/word/document.xml" ContentType="application/vnd.'
                'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            ),
            (
                '<Override PartName="/word/styles.xml" ContentType="application/vnd.'
                'openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            ),
            "</Types>",
        ]
    )


def _root_rels() -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            (
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
                'officeDocument/2006/relationships/officeDocument" '
                'Target="word/document.xml"/>'
            ),
            "</Relationships>",
        ]
    )


def _document_rels() -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            (
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
                'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            ),
            "</Relationships>",
        ]
    )


def _styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
</w:styles>"""
