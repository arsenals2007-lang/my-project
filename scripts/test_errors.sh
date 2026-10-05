#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"
if sh run.sh --vfs examples/minimal.xml --script examples/errors.shell --batch
then
    echo 'Ожидался ненулевой код после ошибок' >&2
    exit 1
fi
if sh run.sh --vfs examples/minimal.xml --script missing.shell --batch
then
    echo 'Ожидалась ошибка чтения скрипта' >&2
    exit 1
fi
