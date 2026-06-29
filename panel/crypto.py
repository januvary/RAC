#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Password-based encryption for the panel's published payload.

The aggregate is encrypted with a key derived from a password (PBKDF2-HMAC-SHA256)
and AES-GCM. The browser decrypts it via Web Crypto using the same parameters,
so Python encrypts and JS decrypts with zero shared library code.

Output format (all fields base64 except iterations):
    iterations : int    (PBKDF2 iteration count)
    salt       : str    (16 bytes, base64)
    nonce      : str    (12 bytes, base64 — AES-GCM IV)
    ciphertext : str    (plaintext + 16-byte GCM auth tag appended, base64)

Note: ``cryptography``'s AESGCM.encrypt emits ciphertext WITH the tag appended,
which is exactly what Web Crypto's AES-GCM decrypt expects. The two sides are
wire-compatible.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DEFAULT_ITERATIONS = 600_000
_KEY_LEN = 32
_SALT_LEN = 16
_NONCE_LEN = 12


def derive_key(
    password: str, salt: bytes, iterations: int = DEFAULT_ITERATIONS
) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_KEY_LEN,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_payload(
    plaintext: bytes, password: str, iterations: int = DEFAULT_ITERATIONS
) -> dict:
    salt = os.urandom(_SALT_LEN)
    key = derive_key(password, salt, iterations)
    nonce = os.urandom(_NONCE_LEN)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return {
        "iterations": iterations,
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }


def decrypt_payload(blob: dict, password: str) -> bytes:
    salt = base64.b64decode(blob["salt"])
    nonce = base64.b64decode(blob["nonce"])
    ciphertext = base64.b64decode(blob["ciphertext"])
    iterations = int(blob.get("iterations", DEFAULT_ITERATIONS))
    key = derive_key(password, salt, iterations)
    return AESGCM(key).decrypt(nonce, ciphertext, None)
