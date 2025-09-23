import React from 'react'
import ReactDOM from 'react-dom/client'
import Index from './pages/Index.tsx'
import PantryTest from './pages/PantryTest.tsx'
import { AuthProvider } from './contexts/AuthContext'
import './globals.css'

// Check if we're on the test route
const isTestRoute = window.location.pathname === '/pantry-test' || window.location.search.includes('test=pantry');

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      {isTestRoute ? <PantryTest /> : <Index />}
    </AuthProvider>
  </React.StrictMode>,
)