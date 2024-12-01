# src/utils/crypto.py

import os
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import jwt

class CryptoManager:
    def __init__(self):
        # Use environment variable for key instead of generating new one
        self.key = os.getenv('ENCRYPTION_KEY')
        if not self.key:
            self.key = self._generate_key()
            # Print key for first-time setup
            print(f"Generated new key: {self.key.decode()}")
        elif isinstance(self.key, str):
            # Convert string key to bytes if loaded from env
            self.key = self.key.encode()
        
        self.backend = default_backend()
        self.salt = os.urandom(16)
        
    def _generate_key(self):
        """Generate a secure encryption key"""
        return Fernet.generate_key()
        
    def _derive_key(self, password, salt):
        """Derive a key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(password.encode())
        
    def encrypt_message(self, message):
        """Encrypt a message using Fernet"""
        f = Fernet(self.key)
        if isinstance(message, str):
            message = message.encode()
        return f.encrypt(message)
        
    def decrypt_message(self, encrypted_message):
        """Decrypt a Fernet-encrypted message"""
        f = Fernet(self.key)
        return f.decrypt(encrypted_message)
        
    def encrypt_data(self, data, password):
        """Encrypt data using AES"""
        key = self._derive_key(password, self.salt)
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Apply padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        
        # Encrypt
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine salt, iv, and encrypted data
        return b64encode(self.salt + iv + encrypted_data).decode('utf-8')
        
    def decrypt_data(self, encrypted_data, password):
        """Decrypt AES-encrypted data"""
        decoded_data = b64decode(encrypted_data.encode('utf-8'))
        
        # Extract salt, iv, and encrypted data
        salt = decoded_data[:16]
        iv = decoded_data[16:32]
        encrypted_data = decoded_data[32:]
        
        # Derive key
        key = self._derive_key(password, salt)
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data.decode('utf-8')
        
    def generate_token(self, payload, secret_key):
        """Generate a JWT token"""
        return jwt.encode(payload, secret_key, algorithm='HS256')
        
    def verify_token(self, token, secret_key):
        """Verify and decode a JWT token"""
        try:
            return jwt.decode(token, secret_key, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return None
            
# Global instance for easy import
crypto_manager = CryptoManager()

# Convenience functions
def encrypt_message(message):
    return crypto_manager.encrypt_message(message)

def decrypt_message(encrypted_message):
    return crypto_manager.decrypt_message(encrypted_message)

def encrypt_data(data, password):
    return crypto_manager.encrypt_data(data, password)

def decrypt_data(encrypted_data, password):
    return crypto_manager.decrypt_data(encrypted_data, password)

def generate_token(payload):
    secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
    return crypto_manager.generate_token(payload, secret_key)

def verify_token(token):
    secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
    return crypto_manager.verify_token(token, secret_key)