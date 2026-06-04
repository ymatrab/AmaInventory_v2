// Framework-free error type so it can be imported in unit tests without
// pulling in next/server.
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message?: string,
  ) {
    super(message ?? code);
  }
}
