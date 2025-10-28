#!/usr/bin/env python3
"""
Generate bad_passwords_hashes.json from bad_passwords.txt

This script reads a list of bad passwords from bad_passwords.txt (one per line)
and generates a JSON file containing SHA1 hash prefixes (first 8 characters)
of each password's lowercase version.

Usage:
    python generate_password_hashes.py [--input INPUT_FILE] [--output OUTPUT_FILE]

Example:
    python generate_password_hashes.py
    python generate_password_hashes.py --input my_passwords.txt --output hashes.json
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Set


def hash_password(password: str, algorithm: str = 'sha1', truncate: int = 8) -> str:
    """
    Hash a password and return truncated hash.

    Args:
        password: The password to hash
        algorithm: Hash algorithm ('sha1' or 'sha256')
        truncate: Number of characters to keep from the hash

    Returns:
        Truncated hash string
    """
    if algorithm == 'sha1':
        hash_obj = hashlib.sha1(password.lower().encode())
    elif algorithm == 'sha256':
        hash_obj = hashlib.sha256(password.lower().encode())
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    return hash_obj.hexdigest()[:truncate]


def read_passwords(input_file: Path) -> Set[str]:
    """
    Read passwords from input file.

    Args:
        input_file: Path to the input file

    Returns:
        Set of passwords (stripped of whitespace)
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    passwords = set()
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            password = line.strip()
            if password and not password.startswith('#'):
                passwords.add(password)

    return passwords


def generate_hash_file(
    input_file: Path,
    output_file: Path,
    algorithm: str = 'sha1',
    truncate: int = 8
) -> None:
    """
    Generate hash file from password list.

    Args:
        input_file: Path to bad passwords text file
        output_file: Path to output JSON file
        algorithm: Hash algorithm to use
        truncate: Number of hash characters to keep
    """
    print(f"Reading passwords from: {input_file}")
    passwords = read_passwords(input_file)
    print(f"Found {len(passwords)} unique passwords")

    print(f"Generating {algorithm.upper()} hashes (truncated to {truncate} chars)...")
    hashes = set()
    for password in passwords:
        hash_value = hash_password(password, algorithm, truncate)
        hashes.add(hash_value)

    # Sort hashes for consistent output
    sorted_hashes = sorted(hashes)

    print(f"Generated {len(sorted_hashes)} unique hash prefixes")

    # Create output data
    output_data = {
        "version": "1.0",
        "algorithm": f"{algorithm}_truncated_{truncate}",
        "count": len(sorted_hashes),
        "hashes": sorted_hashes
    }

    # Write to JSON file
    print(f"Writing hashes to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f)

    print(f"✓ Successfully generated {output_file}")
    print(f"  - Total passwords: {len(passwords)}")
    print(f"  - Unique hashes: {len(sorted_hashes)}")
    print(f"  - Algorithm: {algorithm.upper()}")
    print(f"  - Hash length: {truncate} characters")


def main():
    """Main CLI entry point."""
    # Default paths relative to this script
    script_dir = Path(__file__).parent
    default_input = script_dir / 'bad_passwords.txt'
    default_output = script_dir / 'bad_passwords_hashes.json'

    parser = argparse.ArgumentParser(
        description='Generate bad password hashes for password validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default files (bad_passwords.txt -> bad_passwords_hashes.json)
  python generate_password_hashes.py

  # Specify custom input file
  python generate_password_hashes.py --input my_passwords.txt

  # Specify both input and output
  python generate_password_hashes.py --input passwords.txt --output hashes.json

  # Use SHA256 instead of SHA1
  python generate_password_hashes.py --algorithm sha256

  # Change hash truncation length
  python generate_password_hashes.py --truncate 10
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=default_input,
        help=f'Input file with bad passwords (default: {default_input.name})'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=default_output,
        help=f'Output JSON file (default: {default_output.name})'
    )

    parser.add_argument(
        '--algorithm', '-a',
        choices=['sha1', 'sha256'],
        default='sha1',
        help='Hash algorithm to use (default: sha1)'
    )

    parser.add_argument(
        '--truncate', '-t',
        type=int,
        default=8,
        help='Number of hash characters to keep (default: 8)'
    )

    args = parser.parse_args()

    try:
        generate_hash_file(
            input_file=args.input,
            output_file=args.output,
            algorithm=args.algorithm,
            truncate=args.truncate
        )
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"\nPlease create {args.input} with one password per line.", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
