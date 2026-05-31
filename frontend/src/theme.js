import { createTheme } from '@mui/material/styles'

export default createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3b82f6',
      dark: '#2563eb',
      light: '#60a5fa',
      contrastText: '#fff',
    },
    background: {
      default: '#0c1628',
      paper: '#111f33',
    },
    text: {
      primary: '#e2e8f0',
      secondary: '#94a3b8',
      disabled: '#475569',
    },
    divider: 'rgba(100,136,175,0.15)',
    success: { main: '#22c55e', dark: '#16a34a' },
    error: { main: '#ef4444' },
    warning: { main: '#f59e0b' },
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
          border: '1px solid rgba(100,136,175,0.18)',
          boxShadow: '0 1px 3px 0 rgba(0,0,0,0.4), 0 1px 2px -1px rgba(0,0,0,0.3)',
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
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#0f1d30',
          borderBottom: '1px solid rgba(100,136,175,0.18)',
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: { borderColor: 'rgba(100,136,175,0.15)' },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: { backgroundImage: 'none' },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderColor: 'rgba(100,136,175,0.12)' },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': { backgroundColor: 'rgba(100,136,175,0.05)' },
        },
      },
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined' },
    },
  },
})
