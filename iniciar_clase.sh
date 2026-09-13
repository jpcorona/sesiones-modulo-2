#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Falta el entorno .venv; sigue README.md." >&2
  exit 1
fi
if [[ $# -eq 0 ]]; then
  set -- --query "Incidente de criticidad alta en ERP con error F110-031. Consulta estado y SLA, y explica que revisar segun la documentacion." --trace --json-output work/demo_final.json
fi
exec .venv/bin/python 17_agente_rag.py "$@"
