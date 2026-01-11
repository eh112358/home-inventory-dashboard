$env:Path = "C:\Program Files\Docker\Docker\resources\bin;" + $env:Path
Set-Location "C:\Users\EthanHenkel\Sync\swprojects\charproject\home-inventory"
docker compose build
if ($LASTEXITCODE -eq 0) {
    docker compose up -d
    Write-Host ""
    Write-Host "Application started! Access at http://localhost:828"
    Write-Host "Default password: home123"
}
