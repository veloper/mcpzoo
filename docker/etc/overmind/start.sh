#!/bin/bash

SCRIPT_PATH="$(dirname "$(realpath "$0")")"
SOCKET_FILE_PATH="${SCRIPT_PATH}/.overmind.sock"
PROCFILE_PATH="${SCRIPT_PATH}/Procfile.${APP_ENV}"

# Ensure no stale socket file exists
if [ -f "$SOCKET_FILE_PATH" ]; then
    rm "$SOCKET_FILE_PATH"
fi

exec /usr/local/bin/overmind start --procfile ${PROCFILE_PATH} --socket ${SOCKET_FILE_PATH} "$@"
