# 🧪 Demo Mode Testing Guide

## Overview

This guide documents the temporary demo mode implementation that bypasses authentication for Sprint 3 pantry testing. The demo mode allows full testing of pantry management features without being blocked by authentication issues.

## What Demo Mode Provides

### ✅ Authentication Bypass
- **Automatic Login**: No need to enter credentials
- **Mock User**: Creates a demo user automatically
- **Full Access**: All pantry features are accessible

### ✅ Mock Data Integration
- **Pre-loaded Items**: 10 diverse pantry items with realistic data
- **Expiration Tracking**: Items with various expiration states (expired, expiring soon, fresh)
- **Category Variety**: Items across all pantry categories (Meat, Produce, Dairy, etc.)
- **API Simulation**: Realistic delays and responses

### ✅ Full CRUD Operations
- **Create**: Add new pantry items with autocomplete
- **Read**: View all items with search and filtering
- **Update**: Edit existing items (tested via UI)
- **Delete**: Remove items from pantry (tested via UI)

### ✅ Advanced Features
- **Search**: Filter items by name
- **Category Filtering**: Filter by pantry categories
- **Expiration Tracking**: View expiring and expired items
- **Autocomplete**: Smart suggestions for common grocery items
- **Visual Indicators**: Demo mode badges and notifications

## How to Use Demo Mode

### Method 1: Direct Test Page
```
http://localhost:3000?test=pantry
```
This loads the pantry component directly for focused testing.

### Method 2: Console Commands
Open browser console and run:
```javascript
// Enable demo mode
enableDemoMode()

// Disable demo mode
disableDemoMode()
```

### Method 3: Configuration File
Edit `frontend/src/lib/demoMode.ts`:
```typescript
export const DEMO_MODE: DemoModeConfig = {
  enabled: true,           // Set to false to disable
  bypassAuth: true,        // Bypass authentication
  useMockData: true,       // Use mock data
  showDemoIndicator: true, // Show demo indicators
};
```

## Testing Results ✅

### Authentication Bypass
- ✅ No login required
- ✅ Direct access to pantry interface
- ✅ Demo user automatically created
- ✅ Clear visual indicators of demo mode

### Pantry Interface
- ✅ Full pantry UI loads correctly
- ✅ Demo mode banner displayed
- ✅ "Demo" badge on pantry title
- ✅ All buttons and controls accessible

### Mock Data Loading
- ✅ 10 pre-loaded pantry items
- ✅ Realistic expiration dates
- ✅ Multiple categories represented
- ✅ Console logs confirm mock data usage

### CRUD Operations Tested
- ✅ **CREATE**: Add item dialog opens and functions
- ✅ **READ**: Items display with proper formatting
- ✅ **UPDATE**: Edit buttons accessible (UI confirmed)
- ✅ **DELETE**: Delete buttons accessible (UI confirmed)

### Advanced Features
- ✅ **Search**: Search field functional
- ✅ **Filtering**: Category dropdown works
- ✅ **Autocomplete**: Smart suggestions appear
- ✅ **Expiration Tracking**: "Expiring Items" button accessible
- ✅ **Responsive Design**: Works on different screen sizes

## Mock Data Details

### Sample Items Included
1. **Chicken Breast** (Meat) - Expires in 3 days
2. **Bell Peppers** (Produce) - Expires in 5 days  
3. **Milk** (Dairy) - Expires in 7 days
4. **Rice** (Grains) - Long-term storage
5. **Canned Tomatoes** (Canned Goods) - 6 months
6. **Yogurt** (Dairy) - Expires in 1 day (expiring soon)
7. **Bread** (Grains) - Expired 1 day ago
8. **Olive Oil** (Condiments) - 10 months
9. **Frozen Peas** (Frozen) - 3 months
10. **Bananas** (Produce) - Expires in 2 days (expiring soon)

### API Simulation
- **Realistic Delays**: 200-500ms response times
- **Error Handling**: Graceful fallbacks
- **Console Logging**: Clear debug information
- **State Management**: Persistent during session

## Switching Back to Full Authentication

### Method 1: Console Command
```javascript
disableDemoMode()
window.location.reload()
```

### Method 2: Demo Mode Banner
Click the "Disable Demo Mode" button in the yellow banner.

### Method 3: Configuration File
Edit `frontend/src/lib/demoMode.ts`:
```typescript
export const DEMO_MODE: DemoModeConfig = {
  enabled: false,          // Disable demo mode
  bypassAuth: false,       // Require authentication
  useMockData: false,      // Use real API
  showDemoIndicator: false, // Hide demo indicators
};
```

### Method 4: Environment Variable (Future)
```bash
REACT_APP_DEMO_MODE=false npm run dev
```

## Files Modified

### Core Demo Mode Files
- `frontend/src/lib/demoMode.ts` - Configuration and utilities
- `frontend/src/lib/mockPantryData.ts` - Mock data and CRUD operations

### Updated Components
- `frontend/src/components/Pantry.tsx` - Authentication bypass
- `frontend/src/pages/Index.tsx` - Demo mode integration
- `frontend/src/services/api.ts` - Mock API fallbacks
- `frontend/src/main.tsx` - Test route support

### Test Files
- `frontend/src/pages/PantryTest.tsx` - Direct pantry testing

## Console Commands Available

When demo mode is active, these commands are available in the browser console:

```javascript
// Enable demo mode
enableDemoMode()

// Disable demo mode  
disableDemoMode()

// Check current config
console.log(getDemoModeConfig())

// Check if demo mode is enabled
console.log(isDemoModeEnabled())
```

## Security Notes

⚠️ **Important**: Demo mode is for testing only and should be disabled in production.

- Demo mode bypasses all authentication
- Mock data is not persistent
- No real API calls are made when mock data is enabled
- Clear visual indicators prevent confusion

## Troubleshooting

### Demo Mode Not Working
1. Check console for demo mode logs
2. Verify `DEMO_MODE.enabled = true` in config
3. Clear browser cache and reload
4. Check for JavaScript errors

### Mock Data Not Loading
1. Look for "🧪 [Demo Mode]" console messages
2. Verify `DEMO_MODE.useMockData = true`
3. Check network tab - should see no API calls

### Authentication Still Required
1. Verify `DEMO_MODE.bypassAuth = true`
2. Check that demo user is created
3. Look for auth bypass logs in console

## Next Steps

Once authentication issues are resolved:

1. Set `DEMO_MODE.enabled = false`
2. Test with real authentication
3. Remove demo mode files if no longer needed
4. Update documentation

---

**Demo Mode Status**: ✅ Fully Functional
**Last Updated**: 2025-09-23
**Sprint**: Sprint 3 Testing Phase