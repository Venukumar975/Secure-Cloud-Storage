import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hmac
# Keep this secret locally
MASTER_KEY = b'fixed_32_byte_key_for_testing_123' 

def derive_keys(keyword, master_key=MASTER_KEY):
    """Derives kt1 (search), k2 (file enc), and kv (verification)"""
    keyword_bytes = keyword.lower().encode()
    # Algorithm 1: Key Generation
    kt1 = hmac.new(master_key, keyword_bytes + b"search", hashlib.sha256).digest()[:16]
    k2 = hmac.new(master_key, keyword_bytes + b"file", hashlib.sha256).digest()[:16]
    kv = hmac.new(master_key, keyword_bytes + b"verify", hashlib.sha256).digest()[:16]
    return kt1, k2, kv

def encrypt_file(data, keyword):
    """Algorithm 2: Encrypts data using k2 derived from the keyword."""
    _, k2, _ = derive_keys(keyword) # Updated to skip kv
    aesgcm = AESGCM(k2)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, b'\x00' + data, None)
    return nonce + ciphertext

def decrypt_file(encrypted_data, keyword):
    """Algorithm 6: Decrypts data locally on the client side."""
    _, k2, _ = derive_keys(keyword) # Updated to skip kv
    aesgcm = AESGCM(k2)
    nonce = encrypted_data[:12]
    tag_ciphertext = encrypted_data[12:]
    return aesgcm.decrypt(nonce, tag_ciphertext, None)[1:]