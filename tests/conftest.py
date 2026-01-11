from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock:
        yield mock


@pytest.fixture
def mock_paramiko():
    with patch("paramiko.SSHClient") as mock:
        yield mock


@pytest.fixture
def mock_ansible_runner():
    with patch("ansible_runner.run") as mock:
        yield mock


@pytest.fixture
def mock_fs():
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        with patch("os.path.exists") as mock_exists:
            with patch("os.makedirs") as mock_makedirs:
                yield mock_open, mock_exists, mock_makedirs
