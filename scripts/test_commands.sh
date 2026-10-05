#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"
sh run.sh --vfs examples/deep.xml --script examples/demo.shell --batch
for stage in stage4 stage5
do
    if sh run.sh --vfs examples/deep.xml --script "examples/$stage.shell" --batch
    then
        echo "Скрипт $stage должен сообщить о намеренных ошибках" >&2
        exit 1
    fi
done
