import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode, useSyncExternalStore } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import { createQueryClient } from "./api/queryClient";
import App from "./App.tsx";
import { AuthProvider } from "./auth/AuthProvider";
import { EventsProvider } from "./events/EventsProvider";
import { getApiOrigin, hasApiFallback, subscribeApiOrigin } from "./api/origin";
import "./index.css";

const queryClient = createQueryClient();

function ApiOriginNotice() {
  const origin = useSyncExternalStore(
    subscribeApiOrigin,
    getApiOrigin,
    getApiOrigin,
  );
  if (origin !== "fallback" || !hasApiFallback()) return null;
  return (
    <div
      className="bg-amber-100 px-4 py-2 text-center text-sm text-amber-950"
      role="status"
    >
      Pi API unavailable. Using the Render backup; accounts and data may differ
      from the Pi.
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ApiOriginNotice />
        <AuthProvider>
          <EventsProvider>
            <App />
          </EventsProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
