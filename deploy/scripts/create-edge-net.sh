#!/usr/bin/env bash
# Creates the shared Docker network used by ui-edge, ui-9to18, and copyparse.
set -euo pipefail
NAME=edge_net

if docker network inspect "$NAME" >/dev/null 2>&1; then
  echo "Network '$NAME' already exists."
  exit 0
fi

docker network create "$NAME"
echo "Created network '$NAME'."
