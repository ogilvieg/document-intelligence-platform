import { NextResponse } from "next/server";

const BACKEND_API_URL =
  process.env.BACKEND_API_URL || "http://localhost:8000/api/v1";

export async function GET() {
  try {
    const healthUrl = new URL("/health", BACKEND_API_URL).toString();
    const response = await fetch(healthUrl, {
      cache: "no-store",
      signal: AbortSignal.timeout(45_000),
    });
    const data = await response.json();

    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ status: "unavailable" }, { status: 503 });
  }
}
