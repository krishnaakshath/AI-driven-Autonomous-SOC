import unittest
from unittest.mock import MagicMock, patch
import logging
import sys

# Mock streamlit before importing services
sys.modules["streamlit"] = MagicMock()
import streamlit as st
st.secrets = {}
st.session_state = {}

from services.auth_service import AuthService

class TestAuthService(unittest.TestCase):
    def setUp(self):
        # Prevent actual file I/O
        with patch('os.makedirs'):
            with patch('os.path.exists', return_value=False):
                self.auth = AuthService()
                # Manually inject a user for testing
                self.auth.users = {
                    "test@example.com": {
                        "name": "Test User",
                        "password_hash": "$2b$12$DummyHashForTestingBcrypt............", # Fake bcrypt
                        "password_salt": "legacy_salt",
                        "two_factor_enabled": False
                    }
                }

    def test_hash_password(self):
        """Test password hashing returns a hash."""
        pwd = "securepassword"
        hashed, salt = self.auth._hash_password(pwd)
        self.assertTrue(len(hashed) > 0)
        self.assertTrue(isinstance(hashed, str))
        
        # Verify it works
        self.assertTrue(self.auth._verify_password(pwd, hashed, salt))
        self.assertFalse(self.auth._verify_password("wrong", hashed, salt))

    def test_register_validation(self):
        """Test registration input validation."""
        # Invalid email
        success, msg = self.auth.register("invalid", "pass", "Name")
        self.assertFalse(success)
        self.assertIn("Invalid email", msg)
        
        # Short password
        success, msg = self.auth.register("valid@email.com", "short", "Name")
        self.assertFalse(success)
        self.assertIn("8 characters", msg)

    @patch('services.auth_service.AuthService._save_users')
    def test_register_success(self, mock_save):
        """Test successful registration."""
        success, msg = self.auth.register("new@user.com", "password123", "New User")
        self.assertTrue(success)
        self.assertIn("new@user.com", self.auth.users)
        mock_save.assert_called_once()

    @patch('services.auth_service.AuthService._verify_password')
    @patch('services.auth_service.AuthService._save_users')
    def test_login_success(self, mock_save, mock_verify):
        """Test successful login."""
        mock_verify.return_value = True
        
        success, msg, requires_2fa = self.auth.login("test@example.com", "password")
        self.assertTrue(success)
        # 2FA is False in setup
        self.assertFalse(requires_2fa)

    def test_login_failure(self):
        """Test login with non-existent user."""
        success, msg, _ = self.auth.login("nouser@example.com", "password")
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
