import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = (
  process.env.BACKEND_API_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");
const API_KEY = process.env.API_KEY; // NOT prefixed with NEXT_PUBLIC_

export async function POST(request: NextRequest) {
  try {
    // Get the endpoint from query params
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get("endpoint");

    if (!endpoint) {
      return NextResponse.json(
        { error: "Missing endpoint parameter" },
        { status: 400 },
      );
    }

    // Forward the request to the backend (ensure single slash between base and endpoint)
    const backendUrl = `${BACKEND_URL}/${endpoint.replace(/^\//, "")}`;

    console.log("[Proxy] Forwarding POST request to:", backendUrl);
    console.log("[Proxy] API_KEY present:", !!API_KEY);
    console.log("[Proxy] BACKEND_URL:", BACKEND_URL);

    // Get the request body
    const contentType = request.headers.get("content-type");
    let body;

    if (contentType?.includes("application/json")) {
      body = await request.json();
    } else if (contentType?.includes("multipart/form-data")) {
      body = await request.formData();
    }

    // Forward to backend with API key
    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "X-API-Key": API_KEY || "",
        // Don't forward Content-Type for FormData, fetch sets it automatically
        ...(contentType?.includes("application/json") && {
          "Content-Type": "application/json",
        }),
      },
      body: contentType?.includes("application/json")
        ? JSON.stringify(body)
        : (body as FormData),
    });

    console.log("[Proxy] Backend response status:", response.status);

    // Try to parse response as JSON
    let data;
    try {
      data = await response.json();
    } catch (parseError) {
      console.error(
        "[Proxy] Failed to parse backend response as JSON:",
        parseError,
      );
      const text = await response.text();
      console.error("[Proxy] Backend response text:", text);
      return NextResponse.json(
        { error: "Backend returned invalid response", details: text },
        { status: 500 },
      );
    }

    if (!response.ok) {
      console.error("[Proxy] Backend error:", data);
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("[Proxy] Proxy error:", error);
    console.error("[Proxy] Error details:", {
      message: error instanceof Error ? error.message : "Unknown error",
      stack: error instanceof Error ? error.stack : undefined,
    });
    return NextResponse.json(
      {
        error: "Internal server error",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get("endpoint");

    if (!endpoint) {
      return NextResponse.json(
        { error: "Missing endpoint parameter" },
        { status: 400 },
      );
    }

    const backendUrl = `${BACKEND_URL}/${endpoint.replace(/^\//, "")}`;

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        "X-API-Key": API_KEY || "",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Proxy error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
