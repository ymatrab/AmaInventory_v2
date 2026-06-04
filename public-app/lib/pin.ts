import bcrypt from "bcryptjs";

// Verify an agent PIN against the bcrypt hash pushed from gestion.
// Gestion generates the PIN + hash (Python bcrypt); the $2b$ format is
// interoperable with bcryptjs here.
export function verifyPin(pin: string, pinHash: string): Promise<boolean> {
  return bcrypt.compare(pin, pinHash);
}
