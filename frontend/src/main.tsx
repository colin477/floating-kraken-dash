import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing.tsx'
import Auth from './pages/Auth.tsx'
import Index from './pages/Index.tsx'
import PantryTest from './pages/PantryTest.tsx'
import { AuthProvider } from './contexts/AuthContext'
import './globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/login" element={<Auth />} />
          <Route path="/app" element={<Index />} />
          <Route path="/pantry-test" element={<PantryTest />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)