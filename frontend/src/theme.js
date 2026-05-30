import { createTheme } from '@mui/material/styles'

export default createTheme({
  palette: {
    primary: {
      main: '#2563eb',
      dark: '#1d4ed8',
      light: '#60a5fa',
      contrastText: '#fff',
    },
    background: {
      default: '#f1f5f9',
      paper: '#ffffff',
    },
    text: {
      primary: '#0f172a',
      secondary: '#64748b',
      disabled: '#94a3b8',
    },
    divider: '#e2e8f0',
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      'system-ui',
      'sans-serif',
    ].join(','),
    body2: { lineHeight: 1.75, fontSize: '0.875rem' },
    caption: { letterSpacing: 0.2 },
  },
  shape: { borderRadius: 10 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        '#root': { height: '100vh', display: 'flex', flexDirection: 'column' },
        '*': { boxSizing: 'border-box' },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.04)',
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        sizeLarge: {
          borderRadius: 8,
          fontWeight: 700,
          letterSpacing: 0.4,
          fontSize: '0.9rem',
          padding: '12px 24px',
          textTransform: 'none',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, fontSize: '0.73rem', borderRadius: 6 },
        sizeSmall: { height: 24 },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 8, padding: '6px 14px', fontSize: '0.82rem' },
        message: { padding: '4px 0' },
      },
    },
    MuiSkeleton: {
      defaultProps: { animation: 'wave' },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
    },
    MuiDivider: {
      styleOverrides: {
        root: { borderColor: '#e2e8f0' },
      },
    },
  },
})
