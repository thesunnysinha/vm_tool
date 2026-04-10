import os
from unittest.mock import MagicMock, call, patch

import pytest

from vm_tool.infra.ssh import SSHSetup


def test_ssh_setup_init():
    ssh = SSHSetup("host", "user", "pass", "email@example.com")
    assert ssh.hostname == "host"
    assert ssh.username == "user"
    assert ssh.email == "email@example.com"


@patch("subprocess.run")
def test_ssh_setup_execution(mock_subprocess_run, mock_paramiko, mock_fs):
    mock_open, mock_exists, _ = mock_fs

    # Mock public key does not exist, so it should generate one
    mock_exists.side_effect = lambda p: not p.endswith(".pub")

    ssh = SSHSetup("host", "user", "pass", "email@example.com")

    # Set up exec_command to return (stdin, stdout, stderr) with a successful exit
    mock_client = mock_paramiko.return_value
    mock_stdin = MagicMock()
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()
    mock_stdout.channel.recv_exit_status.return_value = 0
    mock_stderr.read.return_value = b""
    mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

    # Mock reading public key
    mock_open.return_value.__enter__.return_value.read.return_value = "ssh-rsa AAAA..."

    ssh.setup()

    # Check key generation was attempted
    mock_subprocess_run.assert_called_with(
        [
            "ssh-keygen",
            "-t",
            "rsa",
            "-b",
            "4096",
            "-C",
            "email@example.com",
            "-f",
            os.path.expanduser("~/.ssh/id_rsa"),
            "-N",
            "",
        ],
        check=True,
        capture_output=True,
    )

    # Check SSH connection was made
    mock_client.connect.assert_called()

    # Key is now installed via tee -a via stdin (not echo), verify the command
    exec_call_args = mock_client.exec_command.call_args[0][0]
    assert "tee -a ~/.ssh/authorized_keys" in exec_call_args
    assert "mkdir -p ~/.ssh" in exec_call_args

    # Key content written via stdin, not in the command itself
    mock_stdin.write.assert_called_once()
    written = mock_stdin.write.call_args[0][0]
    assert "ssh-rsa AAAA..." in written


@patch("subprocess.run")
def test_ssh_exec_failure_raises(mock_subprocess_run, mock_paramiko, mock_fs):
    """If authorized_keys setup fails on the remote, setup() must raise."""
    mock_open, mock_exists, _ = mock_fs
    mock_exists.side_effect = lambda p: True  # key already exists

    ssh = SSHSetup("10.0.0.1", "ubuntu", "pass", "test@example.com")

    mock_client = mock_paramiko.return_value
    mock_stdin = MagicMock()
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()
    mock_stdout.channel.recv_exit_status.return_value = 1
    mock_stderr.read.return_value = b"Permission denied"
    mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
    mock_open.return_value.__enter__.return_value.read.return_value = "ssh-rsa AAAA..."

    with pytest.raises(RuntimeError, match="Failed to configure authorized_keys"):
        ssh.setup()
