#!/usr/bin/env python3
"""Compatibility wrapper: the vault generator now lives in scripts/vaultlib/.

Keeping this entry point means CI workflows and muscle memory keep working:
    python scripts/build_vault.py --manifest ... --check
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from vaultlib.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
