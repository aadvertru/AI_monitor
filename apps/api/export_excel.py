"""Excel export generation for audit reports."""

from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from apps.api.export_data import ExportReportData
from apps.api.export_openxml import join_values, number, percent, xml_text

Row = list[object]


def generate_excel_export(data: ExportReportData) -> bytes:
    sheets = [
        ("Audit Summary", _summary_rows(data)),
        ("Model Summary", _model_summary_rows(data)),
        ("Answer Matrix", _answer_matrix_rows(data)),
        ("Source Domains", _source_domain_rows(data)),
        ("Source URLs", _source_url_rows(data)),
        ("Concepts Competitors", _concept_competitor_rows(data)),
        ("Diagnostics", _diagnostic_rows(data)),
    ]
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        _write_package_files(archive, sheets)
    return buffer.getvalue()


def _summary_rows(data: ExportReportData) -> list[Row]:
    metadata = data.audit_metadata
    totals = data.summary.totals
    overall = data.summary.overall
    return [
        ["Field", "Value"],
        ["Audit ID", metadata.audit_id],
        ["Brand", metadata.brand_name],
        ["Domain", metadata.brand_domain],
        ["Status", metadata.status],
        ["Generated at", data.generated_at.isoformat()],
        ["Created at", metadata.created_at.isoformat()],
        ["Updated at", metadata.updated_at.isoformat()],
        ["Language", metadata.language],
        ["Country", metadata.country],
        ["Locale", metadata.locale],
        ["Providers", join_values(metadata.providers)],
        ["SCDL level", metadata.scdl_level],
        ["Query count", totals.query_count],
        ["Target count", totals.target_count],
        ["Run count", totals.run_count],
        ["Completed runs", totals.completed_runs],
        ["Failed runs", totals.failed_runs],
        ["Partial runs", totals.partial_runs],
        ["Levels", join_values(totals.levels)],
        ["Mentionability L1", percent(overall.mentionability_l1.percentage)],
        ["Mentionability L2", percent(overall.mentionability_l2.percentage)],
        ["Accuracy L1", percent(overall.accuracy_l1)],
        ["Accuracy L2", percent(overall.accuracy_l2)],
        ["Tone positive", overall.tone.positive],
        ["Tone neutral", overall.tone.neutral],
        ["Tone negative", overall.tone.negative],
        ["Tone unknown", overall.tone.unknown],
    ]


def _model_summary_rows(data: ExportReportData) -> list[Row]:
    rows: list[Row] = [
        [
            "Model",
            "AI family",
            "Execution provider",
            "Model provider",
            "Model ID",
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
                item.ai_family,
                item.execution_provider,
                item.model_provider,
                item.model_id,
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


def _answer_matrix_rows(data: ExportReportData) -> list[Row]:
    rows: list[Row] = [
        [
            "Query",
            "Query type",
            "Target",
            "Level",
            "Model",
            "Execution provider",
            "Status",
            "Answer excerpt",
            "Verdict",
            "Rationale",
            "Score",
            "Sources count",
            "Provider error",
        ]
    ]
    columns = {column.target_id: column for column in data.answer_matrix.columns}
    for row in data.answer_matrix.rows:
        for cell in row.cells:
            column = columns.get(cell.target_id)
            evaluation = cell.evaluation
            rows.append(
                [
                    row.query_text,
                    row.query_type,
                    column.label if column else cell.target_id,
                    column.level if column else "",
                    column.model_id if column else "",
                    column.execution_provider if column else "",
                    cell.status,
                    cell.answer_excerpt,
                    evaluation.verdict if evaluation else "",
                    evaluation.rationale if evaluation else "",
                    number(cell.score),
                    cell.sources_count,
                    cell.provider_error.message if cell.provider_error else "",
                ]
            )
    return rows


def _source_domain_rows(data: ExportReportData) -> list[Row]:
    rows: list[Row] = [
        [
            "Domain",
            "Source count",
            "Unique URL count",
            "Query count",
            "Target count",
            "Levels",
            "Models",
            "Providers",
        ]
    ]
    for domain in data.source_domains.domains:
        rows.append(
            [
                domain.domain,
                domain.source_count,
                domain.unique_url_count,
                domain.query_count,
                domain.target_count,
                join_values(domain.levels),
                join_values(domain.models),
                join_values(domain.providers),
            ]
        )
    return rows


def _source_url_rows(data: ExportReportData) -> list[Row]:
    rows: list[Row] = [
        [
            "Domain",
            "URL",
            "Title",
            "Snippet",
            "Query",
            "Model",
            "Level",
            "Provider",
        ]
    ]
    for domain in data.source_domains.domains:
        for url in domain.urls:
            rows.append(
                [
                    domain.domain,
                    url.normalized_url,
                    url.title,
                    url.snippet,
                    url.query_text,
                    url.model_id,
                    url.level,
                    url.execution_provider,
                ]
            )
    return rows


def _concept_competitor_rows(data: ExportReportData) -> list[Row]:
    rows: list[Row] = [
        ["Type", "Text/name", "Category/domain", "Count/confidence", "Evidence count"]
    ]
    for concept in data.concepts:
        rows.append(
            [
                "concept",
                concept.text,
                concept.category,
                concept.count,
                concept.evidence_count,
            ]
        )
    for candidate in data.competitor_candidates:
        rows.append(
            [
                "competitor_candidate",
                candidate.name,
                candidate.domain,
                number(candidate.confidence),
                candidate.evidence_count,
            ]
        )
    return rows


def _diagnostic_rows(data: ExportReportData) -> list[Row]:
    rows: list[Row] = [
        [
            "Code",
            "Message",
            "Provider",
            "Model",
            "Level",
            "Retryable",
        ]
    ]
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
    return rows


def _write_package_files(archive: ZipFile, sheets: list[tuple[str, list[Row]]]) -> None:
    archive.writestr("[Content_Types].xml", _content_types(len(sheets)))
    archive.writestr("_rels/.rels", _root_rels())
    archive.writestr("xl/workbook.xml", _workbook_xml(sheets))
    archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels(len(sheets)))
    archive.writestr("xl/styles.xml", _styles_xml())
    for index, (_name, rows) in enumerate(sheets, start=1):
        archive.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(rows))


def _content_types(sheet_count: int) -> str:
    sheet_overrides = "\n".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.'
        'worksheet+xml"/>'
        for index in range(1, sheet_count + 1)
    )
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
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.'
                'openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            ),
            (
                '<Override PartName="/xl/styles.xml" ContentType="application/vnd.'
                'openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            ),
            sheet_overrides,
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
                'officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            ),
            "</Relationships>",
        ]
    )


def _workbook_xml(sheets: list[tuple[str, list[Row]]]) -> str:
    sheet_items = "\n".join(
        f'<sheet name="{xml_text(name[:31])}" sheetId="{index}" r:id="rId{index}"/>'
        for index, (name, _rows) in enumerate(sheets, start=1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>{sheet_items}</sheets>
</workbook>"""


def _workbook_rels(sheet_count: int) -> str:
    sheet_rels = "\n".join(
        (
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/'
            "officeDocument/2006/relationships/worksheet\" "
            f'Target="worksheets/sheet{index}.xml"/>'
        )
        for index in range(1, sheet_count + 1)
    )
    style_rel = (
        f'<Relationship Id="rId{sheet_count + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{sheet_rels}
{style_rel}
</Relationships>"""


def _styles_xml() -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            (
                '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
                '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
            ),
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>',
            '<borders count="1"><border/></borders>',
            '<cellStyleXfs count="1"><xf fontId="0" fillId="0" borderId="0"/></cellStyleXfs>',
            (
                '<cellXfs count="2"><xf fontId="0" fillId="0" borderId="0" xfId="0"/>'
                '<xf fontId="1" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            ),
            "</styleSheet>",
        ]
    )


def _sheet_xml(rows: list[Row]) -> str:
    row_xml = "\n".join(
        f'<row r="{row_index}">'
        + "".join(
            _cell_xml(value, bold=row_index == 1)
            for value in row
        )
        + "</row>"
        for row_index, row in enumerate(rows, start=1)
    )
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            (
                '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" '
                'topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
                "</sheetView></sheetViews>"
            ),
            f"<sheetData>{row_xml}</sheetData>",
            "</worksheet>",
        ]
    )


def _cell_xml(value: object, *, bold: bool = False) -> str:
    style = ' s="1"' if bold else ""
    return f'<c t="inlineStr"{style}><is><t>{xml_text(value)}</t></is></c>'
