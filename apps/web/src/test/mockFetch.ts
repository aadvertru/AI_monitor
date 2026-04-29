import { vi } from "vitest";

type MockResponse = {
  body?: unknown;
  status?: number;
  statusText?: string;
};

export function mockFetchSequence(responses: MockResponse[]) {
  const fetchMock = vi.fn();

  for (const response of responses) {
    fetchMock.mockResolvedValueOnce({
      json: async () => response.body,
      ok: !response.status || (response.status >= 200 && response.status < 300),
      status: response.status ?? 200,
      statusText: response.statusText ?? "OK",
    } satisfies Partial<Response>);
  }

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}
