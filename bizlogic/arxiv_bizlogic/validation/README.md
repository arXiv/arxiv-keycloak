# Password Validation

This directory contains precomputed hash tables for validating passwords against a list of commonly used (bad) passwords.

## Files

- **`bad_passwords.txt`** - Original list of 2003 common passwords (one per line)
- **`bad_passwords_hashes.json`** - Precomputed SHA-256 hashes (truncated to 8 chars) - loaded by both Python and TypeScript
- **`password_validator.py`** - Python validator implementation
- **`passwordValidator.ts`** - TypeScript validator implementation (Node.js and Browser)

## Approach

### Why Hash Tables?

1. **Fast Lookup**: O(1) constant time lookup using Set/dict
2. **Compact Storage**: ~40KB for 2003 passwords (vs ~20KB raw text)
3. **Security**: Passwords are hashed, not stored in plaintext
4. **Case-Insensitive**: All passwords converted to lowercase before hashing

### Hash Algorithm

- **Algorithm**: SHA-256 truncated to 8 hexadecimal characters (32 bits)
- **Collision Resistance**: 2^32 possible hashes (~4.3 billion)
- **False Positive Rate**: ~1 in 2.1 million password checks
- **Size**: 8 chars per hash = optimal balance of security and compactness (~24KB total)

## Usage

### Python

```python
from arxiv_bizlogic.validation.password_validator import is_bad_password, validate_password_strength

# Simple check
if is_bad_password("password123"):
    print("Password is too common!")

# With error message
is_valid, error_msg = validate_password_strength("12345678")
if not is_valid:
    print(f"Invalid: {error_msg}")
```

### TypeScript (Node.js)

```typescript
import { isBadPassword, validatePasswordStrength } from './passwordValidator';

// Simple check
if (isBadPassword('password123')) {
  console.log('Password is too common!');
}

// With error message
const result = validatePasswordStrength('12345678');
if (!result.isValid) {
  console.log(`Invalid: ${result.error}`);
}
```

### TypeScript (Browser)

```typescript
import { isBadPasswordBrowser } from './passwordValidator';

// Async check (uses Web Crypto API)
const isBad = await isBadPasswordBrowser('password123');
if (isBad) {
  console.log('Password is too common!');
}
```

## Regenerating Hash File

If you update `bad_passwords.txt`, regenerate the hash file:

```bash
python3 << 'EOF'
import hashlib
import json

with open('bad_passwords.txt', 'r') as f:
    passwords = [line.strip() for line in f if line.strip()]

hashes = sorted(set(hashlib.sha256(pw.lower().encode()).hexdigest()[:8] for pw in passwords))

# JSON for both Python and TypeScript
with open('bad_passwords_hashes.json', 'w') as f:
    json.dump({"version": "1.0", "algorithm": "sha256_truncated_8",
               "count": len(hashes), "hashes": hashes}, f, separators=(',', ':'))

print(f"Generated {len(hashes)} unique hashes")
EOF
```

## Performance

- **Lookup Time**: O(1) - constant time
- **Memory Usage**: ~24KB for hash set
- **Hash Generation**: ~0.001ms per password (negligible overhead)

## Security Notes

1. Passwords are hashed with SHA-256 (one-way function)
2. Truncated hashes provide sufficient uniqueness for 2003 items
3. Case-insensitive comparison prevents bypassing with capitalization
4. Consider adding additional validation rules (length, complexity, etc.)
