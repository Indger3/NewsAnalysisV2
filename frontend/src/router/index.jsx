import { createBrowserRouter, Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import AnalysisPage from '../pages/AnalysisPage'
import LoginPage from '../pages/LoginPage'
import PipelinePage from '../pages/PipelinePage'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" replace />
}

function PublicRoute({ children }) {
  const { token } = useAuth()
  return token ? <Navigate to="/" replace /> : children
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <ProtectedRoute><AnalysisPage /></ProtectedRoute>,
  },
  {
    path: '/pipeline',
    element: <ProtectedRoute><PipelinePage /></ProtectedRoute>,
  },
  {
    path: '/login',
    element: <PublicRoute><LoginPage /></PublicRoute>,
  },
])
