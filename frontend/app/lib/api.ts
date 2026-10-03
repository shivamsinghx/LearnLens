export function apiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (configured && configured.length > 0) {
    return configured;
  }
  return "http://127.0.0.1:8000";
}
