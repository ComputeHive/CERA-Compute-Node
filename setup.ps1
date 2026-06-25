# setup.ps1
$ErrorActionPreference = "Stop"

foreach ($cmd in @("node", "npm", "python3", "poetry", "docker")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "$cmd is not installed"; exit 1
    }
}

Set-Location app/CERA-VM-Manager; npm install
Set-Location ../../backend; poetry install
