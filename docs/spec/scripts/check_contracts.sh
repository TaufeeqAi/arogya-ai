#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python -m pip install -e 'contracts/python[dev]'
python scripts/export_contract_schemas.py
PYTHONPATH=contracts/python pytest -q tests
python -m compileall -q contracts/python
