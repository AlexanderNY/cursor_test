#!/bin/bash
# Creates the shared Docker network used by ui-edge, ui-9to18, and copyparse.
set -euo pipefail

name="edge_net"

exists=$(docker network ls --format '{{.Name}}' | grep -x "$name" || true)
if [ -n "$exists" ]; then
    echo "Network '$name' already exists."
    exit 0
fi

docker network create "$name"
echo "Created network '$name'."
