import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.firewall_shim import FirewallShim

class TestFirewallShim(unittest.TestCase):
    def setUp(self):
        # Prevent actual file I/O
        with patch('os.makedirs'):
            with patch('os.path.exists', return_value=False):
                self.firewall = FirewallShim()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('json.load')
    @patch('os.path.exists')
    def test_block_ip(self, mock_exists, mock_load, mock_dump, mock_file):
        """Test blocking an IP."""
        mock_exists.return_value = True
        mock_load.return_value = []
        
        success = self.firewall.block_ip("1.2.3.4", "Test Reason")
        self.assertTrue(success)
        mock_dump.assert_called()
        
        # Verify call args
        args, _ = mock_dump.call_args
        blocklist = args[0]
        self.assertEqual(len(blocklist), 1)
        self.assertEqual(blocklist[0]["ip"], "1.2.3.4")

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('os.path.exists')
    def test_is_blocked(self, mock_exists, mock_load, mock_file):
        """Test check blocked status."""
        mock_exists.return_value = True
        mock_load.return_value = [
            {"ip": "10.0.0.1", "status": "Active"},
            {"ip": "10.0.0.2", "status": "Disabled"}
        ]
        
        self.assertTrue(self.firewall.is_blocked("10.0.0.1"))
        self.assertFalse(self.firewall.is_blocked("10.0.0.2"))
        self.assertFalse(self.firewall.is_blocked("1.1.1.1"))

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('json.load')
    @patch('os.path.exists')
    def test_unblock_ip(self, mock_exists, mock_load, mock_dump, mock_file):
        """Test unblocking an IP."""
        mock_exists.return_value = True
        mock_load.return_value = [{"ip": "1.2.3.4", "status": "Active"}]
        
        self.firewall.unblock_ip("1.2.3.4")
        
        # Verify list is empty in save call
        args, _ = mock_dump.call_args
        blocklist = args[0]
        self.assertEqual(len(blocklist), 0)

if __name__ == '__main__':
    unittest.main()
