# Pantry API Testing Script
Write-Host "=== EZ Eatin' Pantry API Testing ===" -ForegroundColor Green

# Get authentication token
Write-Host "`n1. Getting authentication token..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body '{"email": "pantrytest@example.com", "password": "testpassword123"}'
    $token = $loginResponse.access_token
    $headers = @{"Authorization" = "Bearer $token"}
    Write-Host "✓ Authentication successful" -ForegroundColor Green
} catch {
    Write-Host "✗ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 1: GET /api/v1/pantry/ (list pantry items)
Write-Host "`n2. Testing GET /api/v1/pantry/ (list pantry items)..." -ForegroundColor Yellow
try {
    $pantryItems = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pantry/" -Method GET -Headers $headers
    Write-Host "✓ GET pantry items successful" -ForegroundColor Green
    Write-Host "   Total items: $($pantryItems.total_count)" -ForegroundColor Cyan
} catch {
    Write-Host "✗ GET pantry items failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: POST /api/v1/pantry/ (add pantry item)
Write-Host "`n3. Testing POST /api/v1/pantry/ (add pantry item)..." -ForegroundColor Yellow
$newItem = @{
    name = "Test Apples"
    category = "produce"
    quantity = 5.0
    unit = "piece"
    expiration_date = "2025-01-15"
    purchase_date = "2025-01-01"
    notes = "Fresh red apples for testing"
} | ConvertTo-Json

$itemId = $null
try {
    $createdItem = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pantry/" -Method POST -Headers $headers -ContentType "application/json" -Body $newItem
    Write-Host "✓ POST pantry item successful" -ForegroundColor Green
    Write-Host "   Created item ID: $($createdItem.id)" -ForegroundColor Cyan
    $itemId = $createdItem.id
} catch {
    Write-Host "✗ POST pantry item failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: GET /api/v1/pantry/{id} (get specific item)
if ($itemId) {
    Write-Host "`n4. Testing GET /api/v1/pantry/$itemId (get specific item)..." -ForegroundColor Yellow
    try {
        $specificItem = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pantry/$itemId" -Method GET -Headers $headers
        Write-Host "✓ GET specific item successful" -ForegroundColor Green
        Write-Host "   Item name: $($specificItem.name)" -ForegroundColor Cyan
    } catch {
        Write-Host "✗ GET specific item failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 4: PUT /api/v1/pantry/{id} (update item)
if ($itemId) {
    Write-Host "`n5. Testing PUT /api/v1/pantry/$itemId (update item)..." -ForegroundColor Yellow
    $updateItem = @{
        quantity = 3.0
        notes = "Updated quantity - some apples consumed"
    } | ConvertTo-Json

    try {
        $updatedItem = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pantry/$itemId" -Method PUT -Headers $headers -ContentType "application/json" -Body $updateItem
        Write-Host "✓ PUT update item successful" -ForegroundColor Green
        Write-Host "   Updated quantity: $($updatedItem.quantity)" -ForegroundColor Cyan
    } catch {
        Write-Host "✗ PUT update item failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 5: GET /api/v1/pantry/expiring/items (expiring items)
Write-Host "`n6. Testing GET /api/v1/pantry/expiring/items (expiring items)..." -ForegroundColor Yellow
try {
    $expiringItems = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pantry/expiring/items" -Method GET -Headers $headers
    Write-Host "✓ GET expiring items successful" -ForegroundColor Green
    Write-Host "   Expiring soon: $($expiringItems.expiring_soon.Count)" -ForegroundColor Cyan
    Write-Host "   Already expired: $($expiringItems.expired.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "✗ GET expiring items failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: GET /api/v1/pantry/stats/overview (statistics)
Write-Host "`n7. Testing GET /api/v1/pantry/stats/overview (statistics)..." -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pantry/stats/overview" -Method GET -Headers $headers
    Write-Host "✓ GET pantry stats successful" -ForegroundColor Green
    Write-Host "   Total items: $($stats.total_items)" -ForegroundColor Cyan
    Write-Host "   Expiring soon: $($stats.expiring_soon_count)" -ForegroundColor Cyan
} catch {
    Write-Host "✗ GET pantry stats failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: GET /api/v1/pantry/search/items (search items)
Write-Host "`n8. Testing GET /api/v1/pantry/search/items (search items)..." -ForegroundColor Yellow
try {
    $searchResults = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pantry/search/items?q=apple" -Method GET -Headers $headers
    Write-Host "✓ GET search items successful" -ForegroundColor Green
    Write-Host "   Search results: $($searchResults.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "✗ GET search items failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 8: DELETE /api/v1/pantry/{id} (delete item)
if ($itemId) {
    Write-Host "`n9. Testing DELETE /api/v1/pantry/$itemId (delete item)..." -ForegroundColor Yellow
    try {
        $deleteResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pantry/$itemId" -Method DELETE -Headers $headers
        Write-Host "✓ DELETE item successful" -ForegroundColor Green
        Write-Host "   Message: $($deleteResult.message)" -ForegroundColor Cyan
    } catch {
        Write-Host "✗ DELETE item failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== Testing Complete ===" -ForegroundColor Green