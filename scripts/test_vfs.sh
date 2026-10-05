#!/bin/sh
set -eu
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"
for source in minimal files deep
do
    sh run.sh --vfs "examples/$source.xml" --script examples/load.shell --batch
done
for source in examples/invalid.xml missing.xml
do
    if sh run.sh --vfs "$source" --script examples/load.shell --batch
    then
        echo "Ожидалась ошибка загрузки $source" >&2
        exit 1
    fi
done
