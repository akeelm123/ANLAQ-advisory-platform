#!/bin/zsh
# Double-click from Finder, or run in Terminal. No secrets in arguments or environment.
set -e
cd -- "$(dirname -- "$0")"
PYTHON="${TCI_PYTHON:-python3}"
LOCAL_PYTHON="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ -z "${TCI_PYTHON:-}" && -x "$LOCAL_PYTHON" ]]; then PYTHON="$LOCAL_PYTHON"; fi
BASE="$HOME/Documents/TCI"
if [[ -z "${TCI_REGISTER:-}" && -f "$BASE/register-reconstruction/outputs/reconstructed-v1/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json" ]]; then export TCI_REGISTER="$BASE/register-reconstruction/outputs/reconstructed-v1/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"; fi
if [[ -z "${TCI_SPEC:-}" && -f "$BASE/validation-specification/outputs/validation-rc1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json" ]]; then export TCI_SPEC="$BASE/validation-specification/outputs/validation-rc1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"; fi
if [[ -z "${TCI_INTERVIEW_SPEC:-}" && -f "INTERVIEW-SPEC-v0.3-preparation.json" ]]; then export TCI_INTERVIEW_SPEC="$PWD/INTERVIEW-SPEC-v0.3-preparation.json"; fi
DATA="${TCI_LOCAL_DATA_DIR:-$HOME/Library/Application Support/ANLAQ-TCI-Synthetic}"
echo "ANLAQ TCI — fictional local pilot only. No real-client records."
echo "Store: $DATA"
SCAN_FLAGS=()
if [[ "${TCI_REQUIRE_MALWARE_SCAN:-0}" == "1" ]]; then
  SCAN_FLAGS=(--require-malware-scan)
  echo "Strict scanning: fresh official definitions required."
fi
if [[ ! -e "$DATA/current.tci" && ! -e "$DATA/salt.bin" ]]; then
  read "ANSWER?Create a new encrypted synthetic local vault and four named accounts? (yes/no): "
  [[ "$ANSWER" == "yes" ]] || exit 0
  exec "$PYTHON" local_pilot.py --data-dir "$DATA" --confirm-synthetic --initialize --auto-port --open-browser "${SCAN_FLAGS[@]}"
fi
exec "$PYTHON" local_pilot.py --data-dir "$DATA" --confirm-synthetic --auto-port --open-browser "${SCAN_FLAGS[@]}"
