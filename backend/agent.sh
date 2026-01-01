#!/bin/bash

SCRIPT_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
APP_PATH=$SCRIPT_DIR

cd $APP_PATH;

export PYTHONPATH="$APP_PATH/src:$PYTHONPATH"
exec uv run python -m src.backend.agent