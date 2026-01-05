import { NextResponse } from "next/server";

/**
 * Diagnostic endpoint to check proxy configuration
 * Remove this in production!
 */
export async function GET() {
  return NextResponse.json({
    configured: {
      BACKEND_API_URL: process.env.BACKEND_API_URL || "NOT SET",
      API_KEY_present: !!process.env.API_KEY,
      API_KEY_length: process.env.API_KEY?.length || 0,
    },
    warning: "Remove this endpoint in production - it exposes configuration",
  });
}
