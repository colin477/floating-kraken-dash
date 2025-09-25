// Toast utility functions for showing notifications
// This is a simple implementation that can be enhanced later

export const showSuccess = (message: string) => {
  // For now, we'll use a simple alert - this can be enhanced with a proper toast library later
  console.log('SUCCESS:', message);
  
  // You can replace this with a proper toast implementation
  // For now, using browser notification as fallback
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('Success', { body: message, icon: '/favicon.ico' });
  } else {
    // Fallback to alert for immediate functionality
    alert(`✅ ${message}`);
  }
};

export const showError = (message: string) => {
  console.error('🔔 [TOAST] showError called with message:', message);
  console.error('🔔 [TOAST] Notification support:', 'Notification' in window);
  console.error('🔔 [TOAST] Notification permission:', 'Notification' in window ? Notification.permission : 'N/A');
  
  if ('Notification' in window && Notification.permission === 'granted') {
    console.error('🔔 [TOAST] Using browser notification');
    new Notification('Error', { body: message, icon: '/favicon.ico' });
  } else {
    console.error('🔔 [TOAST] Falling back to alert() - this might be blocked by browser');
    console.error('🔔 [TOAST] About to show alert with message:', `❌ ${message}`);
    alert(`❌ ${message}`);
    console.error('🔔 [TOAST] Alert should have been displayed');
  }
};

export const showInfo = (message: string) => {
  console.log('INFO:', message);
  
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('Info', { body: message, icon: '/favicon.ico' });
  } else {
    alert(`ℹ️ ${message}`);
  }
};

// Request notification permission on first use
const requestNotificationPermission = () => {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
};

// Auto-request permission
requestNotificationPermission();