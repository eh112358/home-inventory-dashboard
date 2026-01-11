$env:PATH = "C:\Program Files\Docker\Docker\resources\bin;" + $env:PATH
Set-Location "C:\Users\EthanHenkel\Sync\swprojects\charproject\home-inventory"

Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker compose down 2>&1 | Out-Null

Write-Host "Building Docker image..." -ForegroundColor Yellow
docker compose build --no-cache

if ($LASTEXITCODE -eq 0) {
    Write-Host "Starting container..." -ForegroundColor Yellow
    docker compose up -d
    
    Write-Host ""
    Write-Host "Container started successfully!" -ForegroundColor Green
    Write-Host "Access the app at: http://localhost:828" -ForegroundColor Cyan
    Write-Host "Password: HomeInventory2024!" -ForegroundColor Cyan
    Write-Host ""
    docker compose ps
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}
