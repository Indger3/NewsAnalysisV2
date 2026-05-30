import { useState } from 'react'
import { AppBar, Toolbar, Typography, Box, CssBaseline } from '@mui/material'
import ArticlePanel from './components/ArticlePanel'
import ResultsPanel from './components/ResultsPanel'

const API_BASE = 'http://localhost:8000/v1'

const ENDPOINTS = {
  entities:      `${API_BASE}/entities`,
  summary:       `${API_BASE}/summarize`,
  metadata:      `${API_BASE}/metadata`,
  taxonomy:      `${API_BASE}/taxonomy`,
  relationships: `${API_BASE}/relations`,
}

const emptyState = () => ({
  entities: null, summary: null, metadata: null, taxonomy: null, relationships: null,
})
const falseState = () => ({
  entities: false, summary: false, metadata: false, taxonomy: false, relationships: false,
})

export default function App() {
  const [articleText, setArticleText] = useState('')
  const [loading, setLoading]   = useState(falseState())
  const [results, setResults]   = useState(emptyState())
  const [errors, setErrors]     = useState(emptyState())

  const isAnalyzing = Object.values(loading).some(Boolean)

  async function callEndpoint(key, url, body) {
    setLoading((prev) => ({ ...prev, [key]: true }))
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setResults((prev) => ({ ...prev, [key]: data }))
      setErrors((prev)  => ({ ...prev, [key]: null }))
    } catch (err) {
      setErrors((prev)  => ({ ...prev, [key]: err.message }))
      setResults((prev) => ({ ...prev, [key]: null }))
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }))
    }
  }

  function handleAnalyze() {
    const body = { text: articleText }
    setResults(emptyState())
    setErrors(emptyState())
    Object.entries(ENDPOINTS).forEach(([key, url]) => callEndpoint(key, url, body))
  }

  return (
    <>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <AppBar
          position="static"
          sx={{ bgcolor: '#0f172a', borderBottom: '1px solid rgba(255,255,255,0.06)' }}
        >
          <Toolbar sx={{ gap: 2 }}>
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: 1,
                bgcolor: 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <Typography sx={{ color: '#fff', fontWeight: 900, fontSize: '0.75rem', lineHeight: 1 }}>N</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5 }}>
              <Typography sx={{ fontWeight: 800, letterSpacing: -0.3, color: '#fff', fontSize: '1rem' }}>
                NewsAnalysis
              </Typography>
              <Typography sx={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)', fontWeight: 500, letterSpacing: 0.5 }}>
                NLP Pipeline
              </Typography>
            </Box>
          </Toolbar>
        </AppBar>
        <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
          <ArticlePanel
            text={articleText}
            onChange={setArticleText}
            onSubmit={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />
          <ResultsPanel loading={loading} results={results} errors={errors} />
        </Box>
      </Box>
    </>
  )
}
