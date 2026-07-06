$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Push-Location $projectRoot
try {
    Write-Host 'Démarrage du stack Cholera Data Manager...'
    docker compose up -d
    Write-Host ''
    Write-Host 'Services disponibles :'
    Write-Host ' - PostgreSQL : localhost:5432'
    Write-Host ' - pgAdmin    : http://localhost:5050'
    Write-Host ' - pgAdmin    : http://localhost:5050'
}
finally {
    Pop-Location
}
