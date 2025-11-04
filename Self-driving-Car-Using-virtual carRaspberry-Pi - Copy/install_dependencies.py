"""Utility to ensure project Python dependencies are installed.

This script reads the ``requirements.txt`` file and attempts to install any
missing or out-of-date packages using ``pip``. It can be executed directly to
prepare the Python environment for running the project modules.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

import pkg_resources


def parse_requirements(requirements_path: Path) -> List[pkg_resources.Requirement]:
    """Parse requirement specifications from the provided file."""
    requirements: List[pkg_resources.Requirement] = []
    with requirements_path.open("r", encoding="utf-8") as req_file:
        for line in req_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            requirements.append(pkg_resources.Requirement.parse(line))
    return requirements


def is_requirement_satisfied(requirement: pkg_resources.Requirement) -> bool:
    """Return ``True`` if the requirement is already satisfied."""
    try:
        dist = pkg_resources.get_distribution(requirement.project_name)
    except pkg_resources.DistributionNotFound:
        return False

    return dist in requirement


def install_requirement(requirement: pkg_resources.Requirement) -> None:
    """Install a requirement using pip."""
    cmd = [sys.executable, "-m", "pip", "install", str(requirement)]
    subprocess.check_call(cmd)


def ensure_requirements(requirements: Iterable[pkg_resources.Requirement]) -> List[str]:
    """Install missing requirements and return a list of the ones installed."""
    installed: List[str] = []
    for requirement in requirements:
        if is_requirement_satisfied(requirement):
            continue
        install_requirement(requirement)
        installed.append(str(requirement))
    return installed


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install project dependencies if missing")
    parser.add_argument(
        "requirements_file",
        nargs="?",
        default="requirements.txt",
        help="Path to the requirements file (defaults to requirements.txt)",
    )
    args = parser.parse_args(argv)

    requirements_path = Path(args.requirements_file)
    if not requirements_path.exists():
        parser.error(f"Requirements file not found: {requirements_path}")

    os.environ.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")

    requirements = parse_requirements(requirements_path)
    if not requirements:
        print("No dependencies specified; nothing to install.")
        return 0

    try:
        installed = ensure_requirements(requirements)
    except subprocess.CalledProcessError as exc:
        print(f"Failed to install dependency (exit code {exc.returncode}).", file=sys.stderr)
        return exc.returncode

    if installed:
        print("Installed dependencies:")
        for item in installed:
            print(f"  - {item}")
    else:
        print("All dependencies already satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
