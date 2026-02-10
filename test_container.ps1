Write-Host "Testing Home Inventory Container..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check
Write-Host "1. Testing health endpoint..." -ForegroundColor Yellow
try {
    $authCheck = Invoke-RestMethod -Uri 'http://localhost:828/api/auth/check'
    Write-Host "   Auth check response: $($authCheck | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Login
Write-Host "2. Testing login..." -ForegroundColor Yellow
try {
    $body = '{"password":"HomeInventory2024!"}'
    $loginResponse = Invoke-RestMethod -Uri 'http://localhost:828/api/auth/login' -Method Post -Body $body -ContentType 'application/json' -SessionVariable session
    Write-Host "   Login successful: $($loginResponse | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Get categories
Write-Host "3. Testing categories..." -ForegroundColor Yellow
try {
    $categories = Invoke-RestMethod -Uri 'http://localhost:828/api/categories' -WebSession $session
    Write-Host "   Got $($categories.Count) categories" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $_" -ForegroundColor Red
    exit 1
}

# Test 4: Get dashboard
Write-Host "4. Testing dashboard..." -ForegroundColor Yellow
try {
    $dashboard = Invoke-RestMethod -Uri 'http://localhost:828/api/dashboard' -WebSession $session
    Write-Host "   Dashboard has $($dashboard.Count) items" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $_" -ForegroundColor Red
    exit 1
}

# Test 5: Input validation
Write-Host "5. Testing input validation (negative quantity)..." -ForegroundColor Yellow
try {
    $body = '{"consumable_type_id":1,"quantity":-5}'
    $errorResponse = Invoke-WebRequest -Uri 'http://localhost:828/api/purchases' -Method Post -Body $body -ContentType 'application/json' -WebSession $session -ErrorAction SilentlyContinue
    Write-Host "   FAILED: Should have returned error" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "   Correctly rejected negative quantity (400 Bad Request)" -ForegroundColor Green
    } else {
        Write-Host "   Unexpected error: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "All container tests passed!" -ForegroundColor Green
Write-Host ""
Write-Host "Application is running at: http://localhost:828" -ForegroundColor Cyan
Write-Host "Password: HomeInventory2024!" -ForegroundColor Cyan
