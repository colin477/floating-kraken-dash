# Manual Shopping List Creation Test Script
# Step-by-step verification of shopping list functionality

Write-Host "=== Manual Shopping List Creation Test ===" -ForegroundColor Green

# Step 1: Get Authentication Token
Write-Host "`n🔐 Step 1: Getting authentication token..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body '{"email": "pantrytest@example.com", "password": "testpassword123"}'
    $token = $loginResponse.access_token
    $headers = @{"Authorization" = "Bearer $token"; "Content-Type" = "application/json"}
    Write-Host "✅ Token obtained: $($token.Substring(0,20))..." -ForegroundColor Green
} catch {
    Write-Host "❌ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Create Shopping List
Write-Host "`n🛒 Step 2: Creating shopping list..." -ForegroundColor Yellow
$shoppingListData = @{
    title = "Manual Test Shopping List"
    description = "Testing shopping list creation manually"
    items = @(
        @{
            id = "test-item-1"
            name = "Organic Bananas"
            quantity = 6.0
            unit = "pieces"
            category = "produce"
            estimated_price = 3.99
            store = "Whole Foods"
            status = "pending"
            notes = "Look for ripe ones"
        },
        @{
            id = "test-item-2"
            name = "Ground Turkey"
            quantity = 1.0
            unit = "lb"
            category = "meat"
            estimated_price = 5.99
            store = "Whole Foods"
            status = "pending"
        }
    )
    stores = @("Whole Foods")
    budget_limit = 25.0
    shopping_date = "2025-09-26"
    tags = @("manual-test", "verification")
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/shopping-lists/" -Method POST -Headers $headers -Body $shoppingListData
    Write-Host "✅ Shopping List Created Successfully!" -ForegroundColor Green
    Write-Host "   ID: $($response.id)" -ForegroundColor Cyan
    Write-Host "   Title: $($response.title)" -ForegroundColor Cyan
    Write-Host "   Items Count: $($response.items_count)" -ForegroundColor Cyan
    Write-Host "   Total Cost: `$$($response.total_estimated_cost)" -ForegroundColor Cyan
    $listId = $response.id
} catch {
    Write-Host "❌ Shopping list creation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Verify Created Shopping List
Write-Host "`n🔍 Step 3: Verifying created shopping list..." -ForegroundColor Yellow
try {
    $retrievedList = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/shopping-lists/$listId" -Method GET -Headers $headers
    Write-Host "✅ Retrieved Shopping List:" -ForegroundColor Green
    Write-Host "   Title: $($retrievedList.title)" -ForegroundColor Cyan
    Write-Host "   Description: $($retrievedList.description)" -ForegroundColor Cyan
    Write-Host "   Items:" -ForegroundColor Cyan
    foreach ($item in $retrievedList.items) {
        Write-Host "     - $($item.name): $($item.quantity) $($item.unit) @ `$$($item.estimated_price)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Failed to retrieve shopping list: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Test Shopping List Listing
Write-Host "`n📋 Step 4: Testing shopping list listing..." -ForegroundColor Yellow
try {
    $allLists = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/shopping-lists/" -Method GET -Headers $headers
    Write-Host "✅ Total Shopping Lists: $($allLists.total_count)" -ForegroundColor Green
    Write-Host "   Lists found:" -ForegroundColor Cyan
    foreach ($list in $allLists.shopping_lists) {
        Write-Host "     - $($list.title) (ID: $($list.id))" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Failed to list shopping lists: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 5: Clean up (optional)
Write-Host "`n🧹 Step 5: Cleaning up test data..." -ForegroundColor Yellow
try {
    $deleteResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/shopping-lists/$listId" -Method DELETE -Headers $headers
    Write-Host "✅ Test shopping list deleted successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Failed to delete test shopping list: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   (This is not critical - you can delete it manually later)" -ForegroundColor Yellow
}

Write-Host "`n🎉 Manual Shopping List Test Complete!" -ForegroundColor Green
Write-Host "All steps passed successfully. Shopping list creation is working properly." -ForegroundColor Green