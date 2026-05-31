const settings = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  tokenKey:   'na_token',
  userKey:    'na_user',
  appName:    'NewsAnalysis',
  tokenType:  'Bearer',
}

export default settings
