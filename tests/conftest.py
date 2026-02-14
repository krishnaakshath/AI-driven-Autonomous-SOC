import os
import sys
import pytest

# Add project root to path
# This allows tests to import 'services', 'pages', etc.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
