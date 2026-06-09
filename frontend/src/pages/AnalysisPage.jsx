import { useState } from 'react'

import { useNavigate } from 'react-router-dom'
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
  analyzeNormalization,
  analyzeBatch,
} from '../api/nlp.api'

const DEFAULT_NLP_SETTINGS = { model: 'ai4bharat/IndicBERTv2-MLM-only', confidence: 0.6 }

const emptyState = () => ({
  entities: null, summary: null, metadata: null, taxonomy: null, relationships: null,normalization: null,
})
const falseState = () => ({
  entities: false, summary: false, metadata: false, taxonomy: false, relationships: false,normalization: false,
})



export default function AnalysisPage() {
  const [batchFile, setBatchFile] = useState(null)
  const [isBatchMode, setIsBatchMode] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [articleText, setArticleText] = useState('')
  const [loading, setLoading] = useState(falseState())
  const [results, setResults] = useState(emptyState())
  const [errors, setErrors] = useState(emptyState())
  const [nlpSettings, setNlpSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('analysis_settings')
      return saved ? JSON.parse(saved) : DEFAULT_NLP_SETTINGS
    } catch {
      return DEFAULT_NLP_SETTINGS
    }
  })

  const isAnalyzing = Object.values(loading).some(Boolean)

  // function handleSettingsChange(next) {
  //   setNlpSettings(next)
  //   localStorage.setItem('analysis_settings', JSON.stringify(next))
  // }

  async function callEndpoint(key, apiFn, text, options = {}) {
    setLoading((prev) => ({ ...prev, [key]: true }))
    try {
      const res = await apiFn(text, options)
      setResults((prev) => ({ ...prev, [key]: res.data }))
      setErrors((prev) => ({ ...prev, [key]: null }))
    } catch (err) {
      setErrors((prev) => ({ ...prev, [key]: err.message }))
      setResults((prev) => ({ ...prev, [key]: null }))
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }))
    }
  }
async function handleBatchAnalyze() {
  if (!batchFile) return

  try {
    const res = await analyzeBatch(batchFile)

    const blob = new Blob(
      [JSON.stringify(res.data, null, 2)],
      { type: 'application/json' }
    )

    const url = window.URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = 'batch_analysis_results.json'
    a.click()

    window.URL.revokeObjectURL(url)

  } catch (err) {
    console.error(err)
  }
}
  function handleAnalyze() {
    setResults(emptyState())
    setErrors(emptyState())
    callEndpoint('entities', analyzeEntities, articleText)
    callEndpoint('summary', analyzeSummary, articleText, { model: nlpSettings.model })
    callEndpoint('metadata', analyzeMetadata, articleText)
    callEndpoint('taxonomy', analyzeTaxonomy, articleText)
    callEndpoint('relationships', analyzeRelationships, articleText, {
      confidence: nlpSettings.confidence,
      model: nlpSettings.model,
    })
    callEndpoint('normalization', analyzeNormalization, articleText)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar position="static" color="default">
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
            <Typography sx={{ fontWeight: 800, letterSpacing: -0.5, color: 'primary.main', fontSize: '1rem' }}>
              {settings.appName}
            </Typography>
            <Typography sx={{ fontSize: '0.72rem', color: 'text.disabled', fontWeight: 500, letterSpacing: 0.2 }}>
              NLP Pipeline
            </Typography>
          </Box>
          {user?.pages?.some((p) => p.slug === 'pipeline') && (
            <Button
              size="small"
              onClick={() => navigate('/pipeline')}
              sx={{ color: 'text.secondary', fontSize: '0.75rem', textTransform: 'none', '&:hover': { color: 'text.primary' } }}
            >
              Pipeline
            </Button>
          )}
          {user?.pages?.some((p) => p.slug === 'admin') && (
            <Button
              size="small"
              onClick={() => navigate('/admin')}
              sx={{ color: 'text.secondary', fontSize: '0.75rem', textTransform: 'none', '&:hover': { color: 'text.primary' } }}
            >
              Admin
            </Button>
          )}
          {user && (
            <Typography sx={{ fontSize: '0.75rem', color: 'text.disabled', mr: 1 }}>
              {user.email}
            </Typography>
          )}
          <Button
            size="small"
            onClick={logout}
            sx={{ color: 'text.secondary', fontSize: '0.75rem', textTransform: 'none', '&:hover': { color: 'text.primary' } }}
          >
            Sign out
          </Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        {/* <ArticlePanel
          text={articleText}
          onChange={setArticleText}
          onSubmit={handleAnalyze}
          isAnalyzing={isAnalyzing}
          settings={nlpSettings}
          onSettingsChange={handleSettingsChange}
        /> */}
        <ArticlePanel

  text={articleText}

  onChange={setArticleText}

  onSubmit={handleAnalyze}

  isAnalyzing={isAnalyzing}

  // settings={nlpSettings}

  // onSettingsChange={handleSettingsChange}

  batchFile={batchFile}

  onBatchFileSelect={setBatchFile}

  onBatchAnalyze={handleBatchAnalyze}

/>
        <ResultsPanel loading={loading} results={results} errors={errors} />
      </Box>
    </Box>
  )
}
