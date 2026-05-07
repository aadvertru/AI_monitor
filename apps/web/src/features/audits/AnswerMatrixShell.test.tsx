import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { AnswerMatrixResponse } from "../../lib/api/types";
import {
  auditAnswerMatrixFixture,
  providerDiagnosticFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderWithClient } from "../../test/render";
import { AnswerMatrixShell } from "./AnswerMatrixShell";

function renderMatrix(
  matrix: AnswerMatrixResponse = auditAnswerMatrixFixture,
  auditStatus:
    | "created"
    | "running"
    | "partial"
    | "completed"
    | "failed"
    | "cancelled" = "partial",
) {
  const fetchMock = mockFetchSequence([{ body: matrix }]);
  renderWithClient(<AnswerMatrixShell auditId={42} auditStatus={auditStatus} />);
  return fetchMock;
}

const matrixWithStates: AnswerMatrixResponse = {
  ...auditAnswerMatrixFixture,
  columns: [
    ...auditAnswerMatrixFixture.columns,
    {
      target_id: "12",
      label: "Gemini Flash / L1",
      ai_family: "gemini",
      execution_provider: "openrouter",
      model_provider: "google",
      model_id: "google/gemini-2.0-flash-001",
      level: "L1",
      gateway: true,
      gateway_l2_experimental: false,
    },
  ],
  rows: [
    {
      ...auditAnswerMatrixFixture.rows[0]!,
      cells: [
        {
          ...auditAnswerMatrixFixture.rows[0]!.cells[0]!,
          evaluation: {
            verdict: "correct",
            rationale: "Answer matches the known brand facts.",
            confidence: 0.9,
            evaluation_version: "eval-v1",
            evaluated_at: "2026-05-06T00:00:00Z",
          },
          concepts: [
            {
              text: "visibility platform",
              type: "concept",
              category: "known",
              count: 1,
              evidence_count: 1,
            },
          ],
          competitor_candidates: [
            {
              name: "Contoso Monitor",
              domain: "contoso.example",
              confidence: 0.8,
              evidence_type: "comparison",
              evidence_count: 1,
            },
          ],
        },
        auditAnswerMatrixFixture.rows[0]!.cells[1]!,
        {
          target_id: "12",
          run_id: 1003,
          status: "partial",
          answer_excerpt: "Acme AI appears, but the answer is incomplete.",
          brand_mentioned: true,
          score: 0.45,
          evaluation: {
            verdict: "incorrect",
            rationale: "The answer contradicts the known source.",
            confidence: 0.5,
            evaluation_version: "eval-v1",
            evaluated_at: "2026-05-06T00:00:00Z",
          },
          sources_count: 0,
          provider_error: null,
          concepts: [],
          competitor_candidates: [],
        },
      ],
    },
    {
      query_id: "102",
      query_text:
        "brand monitoring platforms with a very long query that should stay contained inside the answer matrix layout",
      query_type: "recommendation",
      cells: [
        {
          target_id: "10",
          run_id: 1004,
          status: "processing",
          answer_excerpt: null,
          brand_mentioned: null,
          score: null,
          evaluation: null,
          sources_count: 0,
          provider_error: null,
          concepts: [],
          competitor_candidates: [],
        },
        {
          target_id: "12",
          run_id: 1005,
          status: "not_run",
          answer_excerpt: null,
          brand_mentioned: null,
          score: null,
          evaluation: {
            verdict: "unknown",
            rationale: null,
            confidence: null,
            evaluation_version: "eval-v1",
            evaluated_at: "2026-05-06T00:00:00Z",
          },
          sources_count: 0,
          provider_error: null,
          concepts: [],
          competitor_candidates: [],
        },
      ],
    },
  ],
};

describe("AnswerMatrixShell", () => {
  it("loads the answer matrix endpoint and renders shell placeholders", async () => {
    const fetchMock = renderMatrix({
      ...auditAnswerMatrixFixture,
      provider_diagnostics: [],
    });

    expect(await screen.findByRole("heading", { name: "Answer matrix" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/answer-matrix",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(screen.getByText("Data source:")).toBeInTheDocument();
    expect(screen.getByText("answer-matrix")).toBeInTheDocument();
    expect(screen.getByText("No provider diagnostics for the matrix.")).toBeInTheDocument();
    expect(screen.getByText("Cell details")).toBeInTheDocument();
    expect(
      screen.getByText("Select a matrix cell to inspect safe normalized details."),
    ).toBeInTheDocument();
  });

  it("renders loading, error, and empty states safely", async () => {
    const fetchMock = vi.fn().mockReturnValue(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);
    const { unmount } = renderWithClient(<AnswerMatrixShell auditId={42} auditStatus="created" />);

    expect(await screen.findByRole("status")).toHaveTextContent("Loading answer matrix...");
    unmount();

    mockFetchSequence([{ body: { detail: "raw_prompt sk-hidden" }, status: 500 }]);
    const errorRender = renderWithClient(
      <AnswerMatrixShell auditId={42} auditStatus="created" />,
    );
    expect(await screen.findByText("Answer matrix unavailable")).toBeInTheDocument();
    expect(screen.queryByText(/raw_prompt|sk-hidden/i)).not.toBeInTheDocument();
    errorRender.unmount();

    renderMatrix({ audit_id: 42, columns: [], rows: [], provider_diagnostics: [] }, "created");
    expect(await screen.findByText("No answer matrix data is available yet.")).toBeInTheDocument();
  });

  it("renders columns, rows, aligned cells, missing placeholders, and gateway metadata", async () => {
    renderMatrix(matrixWithStates);

    expect(await screen.findByText("GPT-4o mini / L1")).toBeInTheDocument();
    expect(screen.getByText("GPT-4o mini with web / L2")).toBeInTheDocument();
    expect(screen.getByText("Gemini Flash / L1")).toBeInTheDocument();
    expect(screen.getAllByText("L2 experimental").length).toBeGreaterThan(0);
    expect(screen.getByText("best ai visibility tools")).toBeInTheDocument();
    expect(screen.getByText(/brand monitoring platforms with a very long query/i)).toBeInTheDocument();
    expect(screen.getByTestId("answer-matrix-scroll")).toBeInTheDocument();
    expect(screen.getAllByText("No cell data.").length).toBeGreaterThan(0);
    expect(screen.getByText("Acme AI appears, but the answer is incomplete.")).toBeInTheDocument();
  });

  it("renders cell content, verdicts, statuses, rationale, source count, and diagnostics", async () => {
    renderMatrix(matrixWithStates);

    expect((await screen.findAllByText("Correct")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Partial").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Incorrect").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Unknown").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Completed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Failed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Processing").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Not run").length).toBeGreaterThan(0);
    expect(screen.getByText("Answer matches the known brand facts.")).toBeInTheDocument();
    expect(screen.getByText("1 source")).toBeInTheDocument();
    expect(screen.getAllByText("OpenAI request timed out.").length).toBeGreaterThan(0);
  });

  it("opens safe excerpt-only details and ignores raw unsafe fields", async () => {
    const user = userEvent.setup();
    renderMatrix({
      ...matrixWithStates,
      rows: [
        {
          ...matrixWithStates.rows[0]!,
          cells: [
            {
              ...matrixWithStates.rows[0]!.cells[0]!,
              raw_response: "raw_response should not render",
              raw_prompt: "raw_prompt should not render",
              raw_tool_result: "raw_tool_result should not render",
              raw_annotations: "raw_annotations should not render",
              headers: { authorization: "Bearer sk-hidden" },
              stack_trace: "traceback sk-hidden",
            } as never,
          ],
        },
      ],
    });

    await user.click(
      await screen.findByRole("button", {
        name: /Open details for best ai visibility tools on GPT-4o mini \/ L1/i,
      }),
    );

    const details = screen.getByRole("complementary");
    expect(within(details).getByText("best ai visibility tools")).toBeInTheDocument();
    expect(within(details).getByText("GPT-4o mini / L1")).toBeInTheDocument();
    expect(within(details).getByText("Safe answer")).toBeInTheDocument();
    expect(within(details).getByText("Acme AI is visible in this answer.")).toBeInTheDocument();
    expect(within(details).getByText("visibility platform")).toBeInTheDocument();
    expect(within(details).getByText("Contoso Monitor")).toBeInTheDocument();
    expect(screen.queryByText(/raw_response|raw_prompt|raw_tool_result|raw_annotations/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/authorization|sk-hidden|traceback/i)).not.toBeInTheDocument();

    await user.click(within(details).getByRole("button", { name: "Close cell details" }));
    expect(screen.getByText("Select a matrix cell to inspect safe normalized details.")).toBeInTheDocument();
  });

  it("filters by level, AI family, model, verdict, query type, and status", async () => {
    const user = userEvent.setup();
    renderMatrix(matrixWithStates);

    await screen.findByRole("heading", { name: "Answer matrix" });

    await user.selectOptions(screen.getByLabelText("Level"), "L2");
    expect(screen.getByText("GPT-4o mini with web / L2")).toBeInTheDocument();
    expect(screen.queryByText("Gemini Flash / L1")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    await user.selectOptions(screen.getByLabelText("AI family"), "gemini");
    expect(screen.getByText("Gemini Flash / L1")).toBeInTheDocument();
    expect(screen.queryByText("GPT-4o mini / L1")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    await user.selectOptions(screen.getByLabelText("Model"), "google/gemini-2.0-flash-001");
    expect(screen.getByText("Gemini Flash / L1")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    await user.selectOptions(screen.getByLabelText("Verdict"), "incorrect");
    expect(screen.getByText("Acme AI appears, but the answer is incomplete.")).toBeInTheDocument();
    expect(screen.queryByText("Acme AI is visible in this answer.")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    await user.selectOptions(screen.getByLabelText("Query type"), "recommendation");
    expect(screen.getByText(/brand monitoring platforms with a very long query/i)).toBeInTheDocument();
    expect(screen.queryByText("best ai visibility tools")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    await user.selectOptions(screen.getByLabelText("Status"), "failed");
    expect(screen.getAllByText("OpenAI request timed out.").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(screen.getByText("Acme AI is visible in this answer.")).toBeInTheDocument();
  });

  it("renders edge state warnings, provider diagnostics, and safe diagnostic fallback", async () => {
    renderMatrix(
      {
        ...matrixWithStates,
        provider_diagnostics: [
          {
            ...providerDiagnosticFixture,
            message: "raw_prompt with sk-hidden",
            details: { raw_response: "unsafe" },
          } as never,
        ],
      },
      "running",
    );

    expect(
      await screen.findByText("The audit is still running. Matrix cells may update as runs finish."),
    ).toBeInTheDocument();
    expect(screen.getByText("Some OpenRouter L2 targets use experimental web-search behavior.")).toBeInTheDocument();
    expect(screen.getByText("Provider issue details are unavailable.")).toBeInTheDocument();
    expect(screen.queryByText(/raw_prompt|raw_response|sk-hidden/i)).not.toBeInTheDocument();
  });

  it("renders partial, failed, and cancelled audit warnings", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        json: async () => matrixWithStates,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>),
    );
    const { unmount } = renderWithClient(<AnswerMatrixShell auditId={42} auditStatus="partial" />);
    expect(
      await screen.findByText("This audit is partial. Completed cells are shown where backend data is available."),
    ).toBeInTheDocument();
    unmount();

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        json: async () => matrixWithStates,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>),
    );
    const failedRender = renderWithClient(<AnswerMatrixShell auditId={42} auditStatus="failed" />);
    expect(
      await screen.findByText("This audit failed. Diagnostics are shown where backend data is available."),
    ).toBeInTheDocument();
    failedRender.unmount();

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        json: async () => matrixWithStates,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>),
    );
    renderWithClient(<AnswerMatrixShell auditId={42} auditStatus="cancelled" />);
    expect(
      await screen.findByText(
        "This audit was cancelled. Completed cells are preserved where backend data is available.",
      ),
    ).toBeInTheDocument();
  });
});
