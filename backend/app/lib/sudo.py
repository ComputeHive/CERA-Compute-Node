"""
Restricted sudo execution utilities for CERA Compute-Node.

Uses ``sudo -n`` (non-interactive) which relies on the NOPASSWD
sudoers policy installed by ``scripts/setup_cera.sh``.

Usage::

    from app.lib.sudo import safe_root, run_root, RootOpError

    # One-shot privileged command
    result = run_root(["debootstrap", "jammy", "/var/vm/rootfs"])

    # With error wrapping
    try:
        safe_root(["mount", "-o", "loop", img, mnt])
    except RootOpError as e:
        logger.error(e)
"""

import subprocess
from typing import List, Optional


class RootOpError(Exception):
    """Raised when a privileged operation fails."""
    pass


def run_root(
    cmd: List[str],
    cwd: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """Run *cmd* under ``sudo -n`` (no password prompt).

    Returns a ``CompletedProcess``; raises ``CalledProcessError`` on
    non-zero exit.
    """
    return subprocess.run(
        ["sudo", "-n"] + cmd,
        check=True,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def safe_root(
    cmd: List[str],
    cwd: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """Like :func:`run_root` but wraps failures in :class:`RootOpError`."""
    try:
        return run_root(cmd, cwd=cwd)
    except subprocess.CalledProcessError as exc:
        raise RootOpError(
            f"{' '.join(cmd)} failed (rc={exc.returncode}): {exc.stderr}"
        ) from exc
    except FileNotFoundError as exc:
        raise RootOpError(f"sudo or command not found: {exc}") from exc
