import { useState } from 'react'
import { AppBar, Toolbar, Typography, Box, Button } from '@mui/material'
import ArticlePanel from '../components/ArticlePanel'
import ResultsPanel from '../components/ResultsPanel'
import { useAuth } from '../contexts/AuthContext'
import settings from '../settings'
import {
  analyzeEntities,
  analyzeSummary,
  analyzeMetadata,
  analyzeTaxonomy,
  analyzeRelationships,
} from '../api/nlp.api'

const emptyState = () => ({
  entities: null, summary: null, metadata: null, taxonomy: null, relationships: null,
})
const falseState = () => ({
  entities: false, summary: false, metadata: false, taxonomy: false, relationships: false,
})

const API_CALLS = {
  entities:      analyzeEntities,
  summary:       analyzeSummary,
  metadata:      analyzeMetadata,
  taxonomy:      analyzeTaxonomy,
  relationships: analyzeRelationships,
}

export default function AnalysisPage() {
  const { user, logout }      = useAuth()
  const [articleText, setArticleText] = useState('')
  const [loading, setLoading]   = useState(falseState())
  const [results, setResults]   = useState(emptyState())
  const [errors, setErrors]     = useState(emptyState())

  const isAnalyzing = Object.values(loading).some(Boolean)

  async function callEndpoint(key, apiFn, text) {
    setLoading((prev) => ({ ...prev, [key]: true }))
    try {
      const res = await apiFn(text)
      setResults((prev) => ({ ...prev, [key]: res.data }))
      setErrors((prev)  => ({ ...prev, [key]: null }))
    } catch (err) {
      setErrors((prev)  => ({ ...prev, [key]: err.message }))
      setResults((prev) => ({ ...prev, [key]: null }))
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }))
    }
  }

  function handleAnalyze() {
    setResults(emptyState())
    setErrors(emptyState())
    Object.entries(API_CALLS).forEach(([key, fn]) => callEndpoint(key, fn, articleText))
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar
        position="static"
        sx={{ bgcolor: '#0f172a', borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <Toolbar sx={{ gap: 2 }}>
          <Box sx={{
            width: 28, height: 28, borderRadius: 1,
            bgcolor: 'primary.main',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Typography sx={{ color: '#fff', fontWeight: 900, fontSize: '0.75rem', lineHeight: 1 }}>N</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5, flexGrow: 1 }}>
            <Typography sx={{ fontWeight: 800, letterSpacing: -0.3, color: '#fff', fontSize: '1rem' }}>
              {settings.appName}
            </Typography>
            <Typography sx={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)', fontWeight: 500 }}>
              NLP Pipeline
            </Typography>
          </Box>
          {user && (
            <Typography sx={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.45)', mr: 1 }}>
              {user.username}
            </Typography>
          )}
          <Button
            size="small"
            onClick={logout}
            sx={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem', textTransform: 'none', '&:hover': { color: '#fff' } }}
          >
            Sign out
          </Button>
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
  )
}
