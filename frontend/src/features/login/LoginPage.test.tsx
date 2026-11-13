import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const state = vi.hoisted(() => ({ pending: false, error: null as unknown }));
vi.mock("@tanstack/react-query", () => ({
  useMutation: () => ({
    isPending: state.pending,
    error: state.error,
    mutate: vi.fn(),
  }),
}));
vi.mock("../../auth/AuthProvider", () => ({
  useAuth: () => ({ auth: null, login: vi.fn() }),
}));
vi.mock("react-router", () => ({
  Navigate: () => null,
  useNavigate: () => vi.fn(),
  useSearchParams: () => [new URLSearchParams()],
}));
import { ApiError } from "../../api/client";
import { LoginPage } from "./LoginPage";

beforeEach(() => {
  state.pending = false;
  state.error = null;
});
describe("login feedback", () => {
  it("identifies CodeIt and marks an in-flight login busy", () => {
    state.pending = true;
    const html = renderToStaticMarkup(<LoginPage />);
    expect(html).toContain("CodeIt");
    expect(html).toContain('aria-busy="true"');
    expect(html).toContain("Logging in…");
    expect(html).toContain("disabled");
  });
  it("announces an invalid login", () => {
    state.error = new ApiError(401, "invalid");
    const html = renderToStaticMarkup(<LoginPage />);
    expect(html).toContain('role="alert"');
    expect(html).toContain("Invalid username or password.");
  });
});
