"""Password validator using precomputed bad password hashes."""

import hashlib
import functools
import json
import os

# Load hashes from JSON file
_HASH_FILE = os.path.join(os.path.dirname(__file__), 'bad_passwords_hashes.json')
with open(_HASH_FILE, 'r') as f:
    _hash_data = json.load(f)
    BAD_PASSWORD_HASHES = set(_hash_data['hashes'])


def is_bad_password(password: str) -> bool:
    """
    Check if a password is in the bad password list.

    Args:
        password: The password to validate (case-insensitive)

    Returns:
        True if password is in the bad list, False otherwise
    """
    password_hash = hashlib.sha256(password.lower().encode()).hexdigest()[:8]
    return password_hash in BAD_PASSWORD_HASHES


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password against bad password list.

    Args:
        password: The password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Too short"

    counts = [0] * 65536
    for c in password:
        if ord(c) < 65536:
            counts[ord(c)] += 1
    max_counts = functools.reduce(max, counts)
    if max_counts >= len(password)/2:
        return False, "Too many repeated characters"

    if is_bad_password(password):
        return False, "This password is too common and not allowed"

    return True, ""


# Example usage
if __name__ == "__main__":
    test_passwords = ["password123", "MyS3cur3P@ss!", "12345678", "unique_password_2024"]

    for pwd in test_passwords:
        is_bad = is_bad_password(pwd)
        print(f"{pwd:30} -> {'BAD' if is_bad else 'OK'}")
