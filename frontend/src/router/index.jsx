import { createBrowserRouter, Navigate } from 'react-router-dom'
import { Box, Typography } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import AdminPage from '../pages/AdminPage'
import AnalysisPage from '../pages/AnalysisPage'
import LoginPage from '../pages/LoginPage'
import PipelinePage from '../pages/PipelinePage'
import SignupPage from '../pages/SignupPage'

function PageRoute({ slug, children }) {
  const { token, user } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  const allowed = user?.pages?.some((p) => p.slug === slug)
  if (!allowed) return <Navigate to="/unauthorized" replace />
  return children
}

function PublicRoute({ children }) {
  const { token } = useAuth()
  return token ? <Navigate to="/" replace /> : children
}

function UnauthorizedPage() {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>Access Denied</Typography>
        <Typography color="text.secondary">You don't have permission to view this page.</Typography>
      </Box>
    </Box>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <PageRoute slug="analysis"><AnalysisPage /></PageRoute>,
  },
  {
    path: '/pipeline',
    element: <PageRoute slug="pipeline"><PipelinePage /></PageRoute>,
  },
  {
    path: '/admin',
    element: <PageRoute slug="admin"><AdminPage /></PageRoute>,
  },
  {
    path: '/login',
    element: <PublicRoute><LoginPage /></PublicRoute>,
  },
  {
    path: '/signup',
    element: <PublicRoute><SignupPage /></PublicRoute>,
  },
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },
])
