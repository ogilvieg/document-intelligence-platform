import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_API_URL || "http://localhost:8000/api/v1";
const API_KEY = process.env.API_KEY; // NOT prefixed with NEXT_PUBLIC_

export async function POST(request: NextRequest) {
  try {
    // Get the endpoint from query params
    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get("endpoint");

    if (!endpoint) {
      return NextResponse.json(
        { error: "Missing endpoint parameter" },
        { status: 400 }
      );
    }

    // Forward the request to the backend
    const backendUrl = `${BACKEND_URL}${endpoint}`;

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

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Proxy error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
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
        { status: 400 }
      );
    }

    const backendUrl = `${BACKEND_URL}${endpoint}`;

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
      { status: 500 }
    );
  }
}
