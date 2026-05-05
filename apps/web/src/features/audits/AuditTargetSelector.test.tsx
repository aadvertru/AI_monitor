import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuditTargetSelector } from "./AuditTargetSelector";
import {
  auditTargetFixture,
  emptyModelCatalogWireFixture,
  extendedModelCatalogWireFixture,
  modelCatalogWireFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { createTestQueryClient } from "../../test/render";

function renderSelector(onChange = vi.fn()) {
  const queryClient = createTestQueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <AuditTargetSelector onChange={onChange} />
    </QueryClientProvider>,
  );
  return { onChange };
}

function renderSelectorWithValue(value = [auditTargetFixture], onChange = vi.fn()) {
  const queryClient = createTestQueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <AuditTargetSelector value={value} onChange={onChange} />
    </QueryClientProvider>,
  );
  return { onChange };
}

function lastTargets(onChange: ReturnType<typeof vi.fn>) {
  const calls = onChange.mock.calls;
  return calls[calls.length - 1]?.[0] ?? [];
}

describe("AuditTargetSelector", () => {
  it("renders loading and error states", async () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));

    const queryClient = createTestQueryClient();
    const { unmount } = render(
      <QueryClientProvider client={queryClient}>
        <AuditTargetSelector onChange={vi.fn()} />
      </QueryClientProvider>,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Loading model catalog");
    unmount();

    mockFetchSequence([{ body: { detail: "Catalog unavailable." }, status: 503 }]);
    renderSelector();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Unable to load model catalog");
    });
  });

  it("renders the default family block and validates empty target selection", async () => {
    mockFetchSequence([{ body: modelCatalogWireFixture }]);
    renderSelector();

    expect(await screen.findByLabelText("AI family 1")).toHaveValue("chatgpt");
    expect(screen.getByText("GPT-4o mini")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Select at least one model target.");
  });

  it("renders an empty catalog fixture", async () => {
    mockFetchSequence([{ body: emptyModelCatalogWireFixture }]);
    renderSelector();

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(
        "No model catalog entries are available.",
      );
    });
  });

  it("renders fixture families including Claude and multiple ChatGPT models", async () => {
    mockFetchSequence([{ body: extendedModelCatalogWireFixture }]);
    const user = userEvent.setup();
    renderSelector();

    expect(await screen.findByText("GPT-4o mini")).toBeInTheDocument();
    expect(screen.getByText("GPT-4.1 nano")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Add family" }));
    expect(screen.getByLabelText("AI family 2")).toHaveValue("gemini");
    await user.click(screen.getByRole("button", { name: "Add family" }));
    expect(screen.getByLabelText("AI family 3")).toHaveValue("claude");
    expect(screen.getByText("Claude 3.5 Sonnet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add family" })).toBeDisabled();
  });

  it("selects models and emits canonical L1/L2 targets", async () => {
    mockFetchSequence([{ body: modelCatalogWireFixture }]);
    const user = userEvent.setup();
    const { onChange } = renderSelector();

    await user.click(await screen.findByLabelText("GPT-4o mini"));
    await user.click(screen.getByLabelText("GPT-4o mini L2"));

    await waitFor(() => expect(lastTargets(onChange)).toHaveLength(2));
    expect(lastTargets(onChange)).toMatchObject([
      {
        aiFamily: "chatgpt",
        executionProvider: "openrouter",
        modelProvider: "openai",
        modelId: "openai/gpt-4o-mini",
        displayName: "GPT-4o mini",
        level: "L1",
        gateway: true,
        gatewayL2Experimental: false,
      },
      {
        aiFamily: "chatgpt",
        modelId: "openai/gpt-4o-mini",
        level: "L2",
        gatewayL2Experimental: true,
      },
    ]);
    expect(screen.getByText("Experimental")).toBeInTheDocument();
  });

  it("adds and removes family blocks", async () => {
    mockFetchSequence([{ body: modelCatalogWireFixture }]);
    const user = userEvent.setup();
    renderSelector();

    await screen.findByLabelText("AI family 1");
    await user.click(screen.getByRole("button", { name: "Add family" }));

    expect(screen.getByLabelText("AI family 2")).toHaveValue("gemini");
    await user.click(screen.getByRole("button", { name: "Remove Gemini" }));
    expect(screen.queryByLabelText("AI family 2")).not.toBeInTheDocument();
  });

  it("disables unsupported L2 and prevents duplicate target output", async () => {
    mockFetchSequence([
      {
        body: {
          families: [
            {
              id: "chatgpt",
              label: "ChatGPT",
              models: [
                {
                  model_id: "openai/gpt-4o-mini",
                  display_name: "GPT-4o mini",
                  model_provider: "openai",
                  execution_provider: "openrouter",
                  ai_family: "chatgpt",
                  supports_l1: true,
                  supports_l2_gateway: false,
                  l2_experimental: false,
                },
              ],
            },
          ],
        },
      },
    ]);
    const user = userEvent.setup();
    const { onChange } = renderSelector();

    await user.click(await screen.findByLabelText("GPT-4o mini"));
    expect(screen.getByLabelText("GPT-4o mini L2")).toBeDisabled();

    await waitFor(() => expect(lastTargets(onChange)).toHaveLength(1));
    await user.click(screen.getByLabelText("GPT-4o mini"));
    await waitFor(() => expect(lastTargets(onChange)).toHaveLength(0));
  });

  it("loads legacy target values into selector state", async () => {
    mockFetchSequence([{ body: modelCatalogWireFixture }]);
    const { onChange } = renderSelectorWithValue();

    expect(await screen.findByLabelText("GPT-4o mini")).toBeChecked();
    expect(screen.getByLabelText("GPT-4o mini L1")).toBeChecked();
    await waitFor(() => expect(lastTargets(onChange)).toHaveLength(1));
    expect(lastTargets(onChange)[0]).toMatchObject({
      aiFamily: "chatgpt",
      modelId: "openai/gpt-4o-mini",
      level: "L1",
    });
  });
});
