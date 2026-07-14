$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Push-Location $projectRoot
try {
    docker compose down
}
finally {
    Pop-Location
}
