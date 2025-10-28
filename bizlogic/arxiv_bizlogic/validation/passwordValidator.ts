/**
 * Password validator using precomputed bad password hashes.
 *
 * Usage:
 *   import { isBadPassword, validatePasswordStrength } from './passwordValidator';
 *
 *   if (isBadPassword('password123')) {
 *     console.log('Password is too common');
 *   }
 */

import * as crypto from 'crypto';
import badPasswordData from './bad_passwords_hashes.json';

// Create a Set for O(1) lookup
const BAD_PASSWORD_HASHES = new Set(badPasswordData.hashes);

/**
 * Check if a password is in the bad password list.
 *
 * @param password - The password to validate (case-insensitive)
 * @returns true if password is in the bad list, false otherwise
 */
export function isBadPassword(password: string): boolean {
  const hash = crypto
    .createHash('sha256')
    .update(password.toLowerCase())
    .digest('hex')
    .substring(0, 8);

  return BAD_PASSWORD_HASHES.has(hash);
}

/**
 * Validate password against bad password list.
 *
 * @param password - The password to validate
 * @returns Object with isValid flag and optional error message
 */
export function validatePasswordStrength(password: string): {
  isValid: boolean;
  error?: string;
} {
  if (isBadPassword(password)) {
    return {
      isValid: false,
      error: 'This password is too common and not allowed'
    };
  }

  return { isValid: true };
}

// Browser-compatible version (no crypto module)
export function isBadPasswordBrowser(password: string): Promise<boolean> {
  return crypto.subtle
    .digest('SHA-256', new TextEncoder().encode(password.toLowerCase()))
    .then(hashBuffer => {
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')
        .substring(0, 8);

      return BAD_PASSWORD_HASHES.has(hashHex);
    });
}

// Example usage
if (require.main === module) {
  const testPasswords = ['password123', 'MyS3cur3P@ss!', '12345678', 'unique_password_2024'];

  console.log('Password Validation Results:');
  testPasswords.forEach(pwd => {
    const isBad = isBadPassword(pwd);
    console.log(`${pwd.padEnd(30)} -> ${isBad ? 'BAD' : 'OK'}`);
  });
}
