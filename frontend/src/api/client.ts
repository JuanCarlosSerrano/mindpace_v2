export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

function getBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL ?? "";
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const base = getBaseUrl();
  const url = path.startsWith("http")
    ? path
    : `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : await res.text();

  if (!res.ok) {
    throw new ApiError(
      `API error ${res.status}`,
      res.status,
      typeof data === "string" ? { message: data } : data
    );
  }

  return data as T;
}

export const client = apiFetch;
