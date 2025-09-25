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
  const config = {
    enabled: true,
    bypassAuth: true,
    useMockData: true,
    showDemoIndicator: true,
  };
  
  // Set both window override and persistent storage
  (window as any).__DEMO_MODE_OVERRIDE__ = config;
  localStorage.setItem('__DEMO_MODE_OVERRIDE__', JSON.stringify(config));
  
  console.log('🧪 Demo Mode ENABLED - Authentication bypassed for testing');
};

export const disableDemoMode = () => {
  const config = {
    enabled: false,
    bypassAuth: false,
    useMockData: false,
    showDemoIndicator: false,
  };
  
  // Set both window override and persistent storage
  (window as any).__DEMO_MODE_OVERRIDE__ = config;
  localStorage.setItem('__DEMO_MODE_OVERRIDE__', JSON.stringify(config));
  
  console.log('🔒 Demo Mode DISABLED - Full authentication required');
};

export const getDemoModeConfig = (): DemoModeConfig => {
  // Check for persistent override in localStorage first
  let persistentOverride = null;
  try {
    const stored = localStorage.getItem('__DEMO_MODE_OVERRIDE__');
    if (stored) {
      persistentOverride = JSON.parse(stored);
    }
  } catch (error) {
    console.warn('[DemoMode] Failed to parse stored demo mode override:', error);
  }
  
  // Allow runtime override via window object for easy testing (takes precedence)
  const windowOverride = (window as any).__DEMO_MODE_OVERRIDE__;
  
  // Priority: window override > localStorage override > default config
  const result = windowOverride || persistentOverride || DEMO_MODE;
  
  // DEBUG: Log demo mode configuration decisions
  console.log('[DemoMode] getDemoModeConfig:', {
    hasWindowOverride: !!windowOverride,
    windowOverride,
    hasPersistentOverride: !!persistentOverride,
    persistentOverride,
    defaultConfig: DEMO_MODE,
    finalResult: result,
    timestamp: new Date().toISOString()
  });
  
  return result;
};

export const isDemoModeEnabled = (): boolean => {
  const result = getDemoModeConfig().enabled;
  console.log('[DemoMode] isDemoModeEnabled:', result);
  return result;
};

export const shouldBypassAuth = (): boolean => {
  const config = getDemoModeConfig();
  const result = config.enabled && config.bypassAuth;
  console.log('[DemoMode] shouldBypassAuth:', { config, result });
  return result;
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