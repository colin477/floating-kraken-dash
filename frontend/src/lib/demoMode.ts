// Demo Mode Configuration for Testing
// This allows bypassing authentication for Sprint 3 testing

export interface DemoModeConfig {
  enabled: boolean;
  bypassAuth: boolean;
  useMockData: boolean;
  showDemoIndicator: boolean;
}

// Demo mode configuration - easily toggle for testing
export const DEMO_MODE: DemoModeConfig = {
  enabled: true,           // Set to false to disable demo mode entirely
  bypassAuth: true,        // Bypass authentication checks
  useMockData: true,       // Use mock data instead of API calls
  showDemoIndicator: true, // Show demo mode indicator in UI
};

// Easy toggle functions for development
export const enableDemoMode = () => {
  (window as any).__DEMO_MODE_OVERRIDE__ = {
    enabled: true,
    bypassAuth: true,
    useMockData: true,
    showDemoIndicator: true,
  };
  console.log('🧪 Demo Mode ENABLED - Authentication bypassed for testing');
};

export const disableDemoMode = () => {
  (window as any).__DEMO_MODE_OVERRIDE__ = {
    enabled: false,
    bypassAuth: false,
    useMockData: false,
    showDemoIndicator: false,
  };
  console.log('🔒 Demo Mode DISABLED - Full authentication required');
};

export const getDemoModeConfig = (): DemoModeConfig => {
  // Allow runtime override via window object for easy testing
  const override = (window as any).__DEMO_MODE_OVERRIDE__;
  return override || DEMO_MODE;
};

export const isDemoModeEnabled = (): boolean => {
  return getDemoModeConfig().enabled;
};

export const shouldBypassAuth = (): boolean => {
  const config = getDemoModeConfig();
  return config.enabled && config.bypassAuth;
};

export const shouldUseMockData = (): boolean => {
  const config = getDemoModeConfig();
  return config.enabled && config.useMockData;
};

export const shouldShowDemoIndicator = (): boolean => {
  const config = getDemoModeConfig();
  return config.enabled && config.showDemoIndicator;
};

// Console helpers for developers
if (typeof window !== 'undefined') {
  (window as any).enableDemoMode = enableDemoMode;
  (window as any).disableDemoMode = disableDemoMode;
  
  console.log('🧪 Demo Mode Helpers Available:');
  console.log('  - enableDemoMode()  - Enable demo mode for testing');
  console.log('  - disableDemoMode() - Disable demo mode, require auth');
}