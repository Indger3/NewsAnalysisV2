import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Alert, Box, Button, Card, CardContent,
  CircularProgress, TextField, Typography,
} from '@mui/material'
import { signup as signupApi } from '../api/auth.api'
import settings from '../settings'

export default function SignupPage() {
  const navigate = useNavigate()
  const [email, setEmail]         = useState('')
  const [name, setName]           = useState('')
  const [password, setPassword]   = useState('')
  const [confirm, setConfirm]     = useState('')
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)

  const passwordMismatch = confirm && password !== confirm

  async function handleSubmit(e) {
    e.preventDefault()
    if (passwordMismatch) return
    setLoading(true)
    setError(null)
    try {
      await signupApi(email, password, name || undefined)
      navigate('/login?registered=1', { replace: true })
    } catch (err) {
      if (err.response?.status === 409) {
        setError('An account with this email already exists.')
      } else {
        setError('Unable to connect. Check that the backend is running.')
      }
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
              bgcolor: '#0f172a',
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

          <Typography variant="h6" fontWeight={700} sx={{ mb: 0.5 }}>Create account</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Fill in your details to register. An admin will assign your access.
          </Typography>

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
              label="Name (optional)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              fullWidth
              autoComplete="name"
              disabled={loading}
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
              autoComplete="new-password"
              disabled={loading}
            />
            <TextField
              label="Confirm password"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              fullWidth
              autoComplete="new-password"
              disabled={loading}
              error={passwordMismatch}
              helperText={passwordMismatch ? 'Passwords do not match' : ''}
            />
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={!email || !password || !confirm || !!passwordMismatch || loading}
              startIcon={loading ? <CircularProgress size={16} color="inherit" /> : null}
              sx={{ mt: 1 }}
            >
              {loading ? 'Creating account…' : 'Create account'}
            </Button>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 3, textAlign: 'center' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'inherit', fontWeight: 600 }}>Sign in</Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
