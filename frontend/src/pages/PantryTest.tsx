import React from 'react';
import { Pantry } from '@/components/Pantry';
import { AuthProvider } from '@/contexts/AuthContext';

const PantryTest = () => {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <div className="p-4 bg-blue-100 border-b border-blue-200">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-lg font-semibold text-blue-800">
              🧪 Pantry Demo Mode Test Page
            </h1>
            <p className="text-sm text-blue-600">
              This page directly loads the Pantry component to test demo mode functionality
            </p>
          </div>
        </div>
        <Pantry onBack={() => console.log('Back clicked')} />
      </div>
    </AuthProvider>
  );
};

export default PantryTest;