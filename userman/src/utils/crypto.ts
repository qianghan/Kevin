import * as crypto from 'crypto';

/**
 * Generates a random token with specified length
 * @param length The length of the token (default: 32)
 * @returns A random token string
 */
export function generateRandomToken(length: number = 32): string {
  return crypto.randomBytes(length).toString('hex');
}

/**
 * Hashes a password using pbkdf2
 * @param password The password to hash
 * @returns A promise that resolves to the hashed password
 */
export async function hashPassword(password: string): Promise<string> {
  // In a real implementation, you would use bcrypt here
  // This is a simplified version for now
  const salt = crypto.randomBytes(16).toString('hex');
  return new Promise((resolve) => {
    crypto.pbkdf2(password, salt, 10000, 64, 'sha512', (err: Error | null, derivedKey: Buffer) => {
      if (err) throw err;
      resolve(salt + ':' + derivedKey.toString('hex'));
    });
  });
}

/**
 * Verifies a password against a hash
 * @param password The password to verify
 * @param hash The hash to verify against
 * @returns A promise that resolves to true if the password matches the hash
 */
export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  // In a real implementation, you would use bcrypt here
  // This is a simplified version for now
  const [salt, key] = hash.split(':');
  return new Promise((resolve) => {
    crypto.pbkdf2(password, salt, 10000, 64, 'sha512', (err: Error | null, derivedKey: Buffer) => {
      if (err) throw err;
      resolve(key === derivedKey.toString('hex'));
    });
  });
} 