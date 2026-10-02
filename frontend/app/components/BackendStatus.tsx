type HealthResponse = {
  status: string;
  service: string;
};

type ApiStatus =
  | { readonly state: "running"; readonly service: string }
  | { readonly state: "unavailable" };

function apiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (configured && configured.length > 0) {
    return configured;
  }
  return "http://127.0.0.1:8000";
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const record = value as Record<string, unknown>;
  return typeof record.status === "string" && typeof record.service === "string";
}

async function readApiStatus(): Promise<ApiStatus> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });

    if (!response.ok) {
      return { state: "unavailable" };
    }

    const payload: unknown = await response.json();
    if (!isHealthResponse(payload) || payload.status !== "ok") {
      return { state: "unavailable" };
    }

    return { state: "running", service: payload.service };
  } catch {
    return { state: "unavailable" };
  }
}

export async function BackendStatus() {
  const status = await readApiStatus();
  const running = status.state === "running";
  const label = running ? `Running (${status.service})` : "Unavailable";

  return (
    <p
      role="status"
      className="inline-flex items-center gap-2 text-sm text-muted"
    >
      <span
        aria-hidden="true"
        className={`size-2 shrink-0 ${running ? "bg-status-running" : "bg-status-unavailable"}`}
      />
      <span>
        Backend status:{" "}
        <span className="font-medium text-foreground">{label}</span>
      </span>
    </p>
  );
}
