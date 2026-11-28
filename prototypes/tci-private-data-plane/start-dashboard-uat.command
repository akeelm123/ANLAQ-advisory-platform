#!/bin/zsh
# Temporary fictional UAT demo. No existing vault is opened or created.
set -e
cd -- "$(dirname -- "$0")"
PYTHON="${TCI_PYTHON:-python3}"
LOCAL_PYTHON="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ -z "${TCI_PYTHON:-}" && -x "$LOCAL_PYTHON" ]]; then PYTHON="$LOCAL_PYTHON"; fi
BASE="$HOME/Documents/TCI"
if [[ -z "${TCI_REGISTER:-}" && -f "$BASE/register-reconstruction/outputs/reconstructed-v1/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json" ]]; then export TCI_REGISTER="$BASE/register-reconstruction/outputs/reconstructed-v1/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"; fi
if [[ -z "${TCI_SPEC:-}" && -f "$BASE/validation-specification/outputs/validation-rc1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json" ]]; then export TCI_SPEC="$BASE/validation-specification/outputs/validation-rc1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"; fi
if [[ -z "${TCI_INTERVIEW_SPEC:-}" && -f "INTERVIEW-SPEC-v0.3-preparation.json" ]]; then export TCI_INTERVIEW_SPEC="$PWD/INTERVIEW-SPEC-v0.3-preparation.json"; fi
if [[ -z "${TCI_INTERVIEW_FIXTURES:-}" && -f "INTERVIEW-GOLDEN-FIXTURES.json" ]]; then export TCI_INTERVIEW_FIXTURES="$PWD/INTERVIEW-GOLDEN-FIXTURES.json"; fi
echo "ANLAQ TCI™ — temporary fictional UAT. The browser will open automatically. Sign in using the generated username and password below."
exec "$PYTHON" simple_preview.py --dashboard --enable-local-model --port 8776 --auto-port --open-browser
