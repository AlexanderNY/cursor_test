# Creates the shared Docker network used by ui-edge, ui-9to18, e2e-tester, and copyparse.
$ErrorActionPreference = "Stop"
$name = "edge_net"

$exists = docker network ls --format "{{.Name}}" | Where-Object { $_ -eq $name }
if ($exists) {
    Write-Host "Network '$name' already exists."
    exit 0
}

docker network create $name
Write-Host "Created network '$name'."
