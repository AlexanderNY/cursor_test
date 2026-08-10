# Generates self-signed TLS certs for local / staging ui-edge.
# Production: replace with real certs (see docs/SSL_CERT_RENEWAL.md).
# Uses host openssl if available, otherwise docker image alpine/openssl.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Certs = Join-Path $Root "certs"

function Invoke-OpenSsl {
    param([string[]]$OpenSslArgs)
    $hostOpenSsl = Get-Command openssl -ErrorAction SilentlyContinue
    if ($hostOpenSsl) {
        & openssl @OpenSslArgs
        if ($LASTEXITCODE -ne 0) { throw "openssl failed: $($OpenSslArgs -join ' ')" }
        return
    }
    $certsUnix = ($Certs -replace '\\', '/') -replace '^([A-Za-z]):', { "/$($_.Groups[1].Value.ToLower())" }
    # Docker Desktop on Windows: K:\... -> /k/...
    if ($Certs -match '^([A-Za-z]):\\') {
        $drive = $Matches[1].ToLower()
        $rest = $Certs.Substring(2) -replace '\\', '/'
        $certsUnix = "/$drive$rest"
    }
    docker run --rm -v "${certsUnix}:/certs" alpine/openssl @OpenSslArgs
    if ($LASTEXITCODE -ne 0) { throw "docker openssl failed: $($OpenSslArgs -join ' ')" }
}

function New-SiteCert {
    param(
        [string]$SiteDir,
        [string[]]$DnsNames
    )
    $dir = Join-Path $Certs $SiteDir
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $keyHost = Join-Path $dir "privkey.pem"
    $crtHost = Join-Path $dir "fullchain.pem"
    if ((Test-Path $keyHost) -and (Test-Path $crtHost)) {
        Write-Host "Skip $SiteDir (already has fullchain.pem + privkey.pem)"
        return
    }
    $san = ($DnsNames | ForEach-Object { "DNS:$_" }) -join ","
    $key = "/certs/$SiteDir/privkey.pem"
    $crt = "/certs/$SiteDir/fullchain.pem"
    $hostOpenSsl = Get-Command openssl -ErrorAction SilentlyContinue
    if ($hostOpenSsl) {
        $key = $keyHost
        $crt = $crtHost
    }
    Invoke-OpenSsl @(
        "req", "-x509", "-nodes", "-newkey", "rsa:2048", "-days", "825",
        "-keyout", $key, "-out", $crt,
        "-subj", "/CN=$($DnsNames[0])",
        "-addext", "subjectAltName=$san"
    )
    Write-Host "Created $SiteDir certs for: $($DnsNames -join ', ')"
}

New-SiteCert -SiteDir "copyparse" -DnsNames @("copyparse.ru", "www.copyparse.ru")
New-SiteCert -SiteDir "9to18" -DnsNames @("9to18.ru", "www.9to18.ru")
Write-Host "Done. Restart ui-edge after installing certs."
