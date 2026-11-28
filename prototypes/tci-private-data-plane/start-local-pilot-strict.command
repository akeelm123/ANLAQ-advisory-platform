#!/bin/zsh
# Fictional local pilot only, fail closed on upload if scanner unavailable.
set -e
cd -- "$(dirname -- "$0")"
export TCI_REQUIRE_MALWARE_SCAN=1
exec ./start-local-pilot.command
