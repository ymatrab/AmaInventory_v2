import { NextResponse } from "next/server";
import { ZodError } from "zod";

import { ApiError } from "./errors";

export { ApiError } from "./errors";

// Consistent error envelope, mirroring the gestion side:
// { "error": { "code": ..., "detail": ... } }
export function errorResponse(err: unknown): NextResponse {
  if (err instanceof ApiError) {
    return NextResponse.json(
      { error: { code: err.code, detail: err.message } },
      { status: err.status },
    );
  }
  if (err instanceof ZodError) {
    return NextResponse.json(
      { error: { code: "validation_error", detail: err.flatten() } },
      { status: 400 },
    );
  }
  console.error(err);
  return NextResponse.json(
    { error: { code: "internal", detail: "Internal server error" } },
    { status: 500 },
  );
}
