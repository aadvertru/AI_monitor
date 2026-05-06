import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  auditDetailFixture,
  auditListFixture,
  auditResultsFixture,
  auditSummaryFixture,
  currentUserFixture,
  modelCatalogWireFixture,
} from "./fixtures";
import { mockFetchSequence } from "./mockFetch";
import { renderRoute } from "./render";

describe("i18n regression coverage", () => {
  it("renders the audits dashboard in English and Russian with persisted switching", async () => {
    mockFetchSequence([{ body: currentUserFixture }, { body: auditListFixture }]);
    const user = userEvent.setup();

    renderRoute("/audits");

    expect(await screen.findByRole("heading", { name: "Audits" })).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Interface language"), "ru");

    expect(await screen.findByRole("heading", { name: "Аудиты" })).toBeInTheDocument();
    expect(localStorage.getItem("ai-monitor.locale")).toBe("ru");
  });

  it("renders create-audit labels and validation in Russian", async () => {
    mockFetchSequence([{ body: currentUserFixture }, { body: modelCatalogWireFixture }]);
    const user = userEvent.setup();

    renderRoute("/audits/new");

    await screen.findByRole("heading", { name: "Create audit" });
    await user.selectOptions(screen.getByLabelText("Interface language"), "ru");
    await user.click(screen.getByRole("button", { name: "Создать аудит" }));

    expect(await screen.findByText("Введите название бренда.")).toBeInTheDocument();
    expect(screen.getByText("Целевые AI-модели")).toBeInTheDocument();
  });

  it("translates status and summary labels while preserving raw user content", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    await screen.findByRole("heading", { name: "Acme AI" });
    await user.selectOptions(screen.getByLabelText("Interface language"), "ru");

    expect(await screen.findByText("Завершён")).toBeInTheDocument();
    expect(screen.getByText("Настройки аудита")).toBeInTheDocument();
    expect(screen.getAllByText("best ai visibility tools")).not.toHaveLength(0);
    expect(screen.getByText("AI visibility monitoring platform.")).toBeInTheDocument();
  });

  it("translates results labels while preserving raw query, provider id, and source title", async () => {
    mockFetchSequence([{ body: currentUserFixture }, { body: auditResultsFixture }]);
    const user = userEvent.setup();

    renderRoute("/audits/42/results");

    await screen.findByRole("heading", { name: "Audit results" });
    await user.selectOptions(screen.getByLabelText("Interface language"), "ru");

    expect(await screen.findByRole("heading", { name: "Результаты аудита" })).toBeInTheDocument();
    expect(screen.getByText("best ai visibility tools")).toBeInTheDocument();
    expect(screen.getAllByText("mock")).not.toHaveLength(0);
    await user.click(screen.getAllByRole("button", { name: "Детали" })[0]);
    expect(screen.getAllByText(/example.com/)).not.toHaveLength(0);
  });

  it("falls back safely from an invalid stored locale", async () => {
    localStorage.setItem("ai-monitor.locale", "xx");
    mockFetchSequence([{ body: currentUserFixture }, { body: auditListFixture }]);

    renderRoute("/audits");

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Audits" })).toBeInTheDocument();
    });
  });
});
