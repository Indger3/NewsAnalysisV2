import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import {
  Alert, Box, Button, Card, CardContent,
  CircularProgress, TextField, Typography,
} from '@mui/material'
import { login as loginApi } from '../api/auth.api'
import { useAuth } from '../contexts/AuthContext'
import settings from '../settings'

export default function LoginPage() {
  const navigate            = useNavigate()
  const [params]            = useSearchParams()
  const { login }           = useAuth()
  const [email, setEmail]   = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  const justRegistered = params.get('registered') === '1'

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await loginApi(email, password)
      login(res.data.access_token, res.data.user)
      navigate('/', { replace: true })
    } catch (err) {
      setError(
        err.response?.status === 401
          ? 'Invalid credentials. Please try again.'
          : 'Unable to connect. Check that the backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      bgcolor: 'background.default',
    }}>
      <Card sx={{ width: 400 }}>
        <CardContent sx={{ p: 4, '&:last-child': { pb: 4 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 4 }}>
            <Box sx={{
              width: 34, height: 34, borderRadius: 1,
              bgcolor: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(100,136,175,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <Box sx={{ width: 18, height: 18, borderRadius: 0.5, bgcolor: 'primary.main' }} />
            </Box>
            <Box>
              <Typography sx={{ fontWeight: 800, fontSize: '1rem', letterSpacing: -0.3, lineHeight: 1.1 }}>
                {settings.appName}
              </Typography>
              <Typography variant="caption" color="text.secondary">NLP Pipeline</Typography>
            </Box>
          </Box>

          <Typography variant="h6" fontWeight={700} sx={{ mb: 0.5 }}>Sign in</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Enter your credentials to continue.
          </Typography>

          {justRegistered && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Account created! Sign in to continue.
            </Alert>
          )}
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              fullWidth
              autoFocus
              autoComplete="email"
              disabled={loading}
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
              autoComplete="current-password"
              disabled={loading}
            />
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={!email || !password || loading}
              startIcon={loading ? <CircularProgress size={16} color="inherit" /> : null}
              sx={{ mt: 1 }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 3, textAlign: 'center' }}>
            Don't have an account?{' '}
            <Link to="/signup" style={{ color: 'inherit', fontWeight: 600 }}>Sign up</Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
