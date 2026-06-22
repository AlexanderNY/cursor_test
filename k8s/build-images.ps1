# Build all images for Minikube. Run from cursor_test (project root).
# First run: minikube -p minikube docker-env | Invoke-Expression

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$builds = @(
    @{ Name = "gateway"; Path = ".\api-gateway" },
    @{ Name = "auth"; Path = ".\auth" },
    @{ Name = "core"; Path = ".\core" },
    @{ Name = "scheduler"; Path = ".\scheduler" },
    @{ Name = "ui"; Path = ".\ui-app" },
    @{ Name = "tg-bot"; Path = ".\tg-bot" },
    @{ Name = "wp-bot"; Path = ".\wp-bot" },
    @{ Name = "url-bot"; Path = ".\url-bot" },
    @{ Name = "collector"; Path = ".\collector" },
    @{ Name = "processor"; Path = ".\processor" },
    @{ Name = "th-bot"; Path = ".\th-bot" },
    @{ Name = "selectcb"; Path = ".\selectcb" }
)

foreach ($b in $builds) {
    Write-Host "Building $($b.Name):latest from $($b.Path)..."
    docker build -t "$($b.Name):latest" $b.Path
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host "All images built."
