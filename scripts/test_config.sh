#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"
sh run.sh --batch
sh run.sh --vfs examples/minimal.xml --batch
sh run.sh --script examples/stage2.shell --batch
sh run.sh --vfs examples/minimal.xml --script examples/stage2.shell --batch
