#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for Flask application
"""

import secrets
import string

def generate_secret_key(length=64):
    """
    Generate a cryptographically secure random string for Flask SECRET_KEY
    
    Args:
        length: Length of the secret key (default 64 characters)
        
    Returns:
        str: Secure random string
    """
    # Use letters, digits, and some safe special characters
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    
    # Generate cryptographically secure random string
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return secret_key

if __name__ == '__main__':
    print("🔐 Generating secure Flask SECRET_KEY...")
    print()
    
    # Generate different lengths
    keys = {
        'Short (32 chars)': generate_secret_key(32),
        'Medium (64 chars)': generate_secret_key(64), 
        'Long (128 chars)': generate_secret_key(128)
    }
    
    for name, key in keys.items():
        print(f"{name}:")
        print(f"SECRET_KEY={key}")
        print()
    
    print("💡 Recommended: Use the 64-character key for production")
    print("⚠️  Keep this secret! Never commit to version control!")
    print()
    print("📝 To use:")
    print("1. Copy one of the keys above")
    print("2. Update SECRET_KEY in your .env file")
    print("3. Restart your Flask application")