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
  console.error('ERROR:', message);
  
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('Error', { body: message, icon: '/favicon.ico' });
  } else {
    alert(`❌ ${message}`);
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