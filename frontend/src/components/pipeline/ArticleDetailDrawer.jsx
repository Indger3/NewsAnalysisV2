import { useEffect, useState } from 'react'
import {
  Box,
  Chip,
  CircularProgress,
  Drawer,
  IconButton,
  Stack,
  Step,
  StepContent,
  StepLabel,
  Stepper,
  Tab,
  Tabs,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutlined'
import { getArticle, getArticleResults } from '../../api/pipeline.api'

const ENTITY_STYLES = {
  PERSON:  { bg: '#ede9fe', color: '#5b21b6', border: '#c4b5fd' },
  ORG:     { bg: '#dbeafe', color: '#1d4ed8', border: '#93c5fd' },
  GPE:     { bg: '#d1fae5', color: '#065f46', border: '#6ee7b7' },
  LOC:     { bg: '#d1fae5', color: '#065f46', border: '#6ee7b7' },
  PRODUCT: { bg: '#e0f2fe', color: '#075985', border: '#7dd3fc' },
  EVENT:   { bg: '#fce7f3', color: '#9d174d', border: '#f9a8d4' },
}
const DEFAULT_STYLE = { bg: '#f1f5f9', color: '#475569', border: '#cbd5e1' }

function durationLabel(step) {
  if (!step.started_at || !step.completed_at) return null
  const ms = new Date(step.completed_at) - new Date(step.started_at)
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}

function StepIcon({ status }) {
  if (status === 'completed') return <CheckCircleIcon sx={{ color: '#22c55e', fontSize: 20 }} />
  if (status === 'failed')    return <ErrorIcon sx={{ color: '#ef4444', fontSize: 20 }} />
  if (status === 'skipped')   return <RemoveCircleOutlineIcon sx={{ color: '#64748b', fontSize: 20 }} />
  if (status === 'running')   return <CircularProgress size={18} thickness={5} />
  return null  // pending — default stepper icon
}

function ProcessingTab({ run }) {
  if (!run) {
    return (
      <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic', mt: 2 }}>
        Pipeline has not been triggered yet.
      </Typography>
    )
  }

  const steps = run.steps ?? []
  const activeStep = steps.findIndex((s) => s.status === 'running')

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
        <Typography variant="caption" color="text.secondary">
          Workflow: <strong>{run.workflow_name}</strong> v{run.workflow_version}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          · Triggered: {new Date(run.triggered_at).toLocaleString()}
        </Typography>
        {run.completed_at && (
          <Typography variant="caption" color="text.secondary">
            · Done: {new Date(run.completed_at).toLocaleString()}
          </Typography>
        )}
      </Stack>

      <Stepper activeStep={activeStep === -1 ? steps.length : activeStep} orientation="vertical">
        {steps.map((step) => {
          const dur = durationLabel(step)
          const isError = step.status === 'failed'
          return (
            <Step key={step.step_exec_id} completed={step.status === 'completed'}>
              <StepLabel
                error={isError}
                icon={<StepIcon status={step.status} />}
                optional={
                  dur ? (
                    <Typography variant="caption" color="text.secondary">{dur}</Typography>
                  ) : step.status === 'skipped' ? (
                    <Typography variant="caption" color="text.disabled">skipped</Typography>
                  ) : null
                }
              >
                <Typography sx={{ fontSize: '0.82rem', textTransform: 'capitalize', fontWeight: 600 }}>
                  {step.step_name}
                </Typography>
              </StepLabel>
              {isError && (
                <StepContent>
                  <Typography variant="caption" color="error" sx={{ fontFamily: 'monospace' }}>
                    {step.error_message}
                  </Typography>
                </StepContent>
              )}
            </Step>
          )
        })}
      </Stepper>
    </Box>
  )
}

function ResultsTab({ articleId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getArticleResults(articleId)
      .then((res) => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [articleId])

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>
  if (!data) return <Typography color="text.disabled" sx={{ mt: 2, fontStyle: 'italic' }}>No results available.</Typography>

  const grouped = {}
  for (const { entity, label } of data.entities ?? []) {
    if (!grouped[label]) grouped[label] = []
    grouped[label].push(entity)
  }

  return (
    <Stack spacing={3}>
      {data.summary && (
        <Box>
          <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: 1 }}>Summary</Typography>
          <Box sx={{ mt: 0.5, p: 1.5, borderLeft: '3px solid', borderColor: 'primary.main', bgcolor: 'rgba(59,130,246,0.08)', borderRadius: '0 6px 6px 0' }}>
            <Typography variant="body2" sx={{ lineHeight: 1.7 }}>{data.summary}</Typography>
          </Box>
        </Box>
      )}

      {Object.keys(grouped).length > 0 && (
        <Box>
          <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: 1 }}>Entities</Typography>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            {Object.entries(grouped).map(([label, items]) => {
              const style = ENTITY_STYLES[label] ?? DEFAULT_STYLE
              return (
                <Box key={label}>
                  <Box sx={{ display: 'inline-flex', px: 0.75, py: 0.25, mb: 0.5, borderRadius: '4px', bgcolor: style.bg, border: `1px solid ${style.border}` }}>
                    <Typography sx={{ fontSize: '0.62rem', fontWeight: 800, letterSpacing: 0.8, color: style.color }}>{label}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                    {items.map((item) => (
                      <Chip key={item} label={item} size="small"
                        sx={{ bgcolor: style.bg, color: style.color, border: `1px solid ${style.border}` }} />
                    ))}
                  </Box>
                </Box>
              )
            })}
          </Stack>
        </Box>
      )}

      {data.relationships?.length > 0 && (
        <Box>
          <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: 1 }}>Relationships</Typography>
          <Stack spacing={1} sx={{ mt: 0.5 }}>
            {data.relationships.map(({ subj, verb, obj, confidence }, i) => (
              <Stack key={i} direction="row" alignItems="center" gap={1} flexWrap="wrap">
                <Chip label={subj} size="small" sx={{ bgcolor: '#dbeafe', color: '#1d4ed8', border: '1px solid #93c5fd' }} />
                <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', fontStyle: 'italic' }}>→ {verb} →</Typography>
                <Chip label={obj} size="small" sx={{ bgcolor: '#ede9fe', color: '#5b21b6', border: '1px solid #c4b5fd' }} />
                {confidence != null && (
                  <Typography sx={{ fontSize: '0.65rem', color: 'text.disabled' }}>{(confidence * 100).toFixed(0)}%</Typography>
                )}
              </Stack>
            ))}
          </Stack>
        </Box>
      )}
    </Stack>
  )
}

function ArticleTab({ articleId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getArticle(articleId)
      .then((res) => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [articleId])

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>
  if (!data) return <Typography color="text.disabled" sx={{ mt: 2, fontStyle: 'italic' }}>Failed to load article.</Typography>

  return (
    <Stack spacing={2}>
      <Box>
        {data.title && (
          <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1rem', mb: 0.5 }}>{data.title}</Typography>
        )}
        <Stack direction="row" spacing={2} flexWrap="wrap">
          <Typography variant="caption" color="text.secondary">Source: {data.source}</Typography>
          {data.published_at && (
            <Typography variant="caption" color="text.secondary">
              Published: {new Date(data.published_at).toLocaleDateString()}
            </Typography>
          )}
          {data.word_count && (
            <Typography variant="caption" color="text.secondary">{data.word_count.toLocaleString()} words</Typography>
          )}
          {data.language && (
            <Typography variant="caption" color="text.secondary">Lang: {data.language.toUpperCase()}</Typography>
          )}
        </Stack>
      </Box>
      <Typography variant="body2" sx={{ lineHeight: 1.8, whiteSpace: 'pre-wrap', color: 'text.secondary' }}>
        {data.body}
      </Typography>
    </Stack>
  )
}

const TAB_LABELS = ['article', 'processing', 'results']

export default function ArticleDetailDrawer({ open, article, initialTab, run, onClose }) {
  const [tab, setTab] = useState(0)

  useEffect(() => {
    if (open && initialTab) {
      setTab(TAB_LABELS.indexOf(initialTab))
    }
  }, [open, initialTab])

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: '100vw', sm: 520 },
          bgcolor: 'background.paper',
          borderLeft: '1px solid rgba(100,136,175,0.18)',
          p: 0,
        },
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* header */}
        <Box sx={{ px: 2.5, pt: 2, pb: 1, borderBottom: '1px solid rgba(100,136,175,0.15)', display: 'flex', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography noWrap sx={{ fontWeight: 700, fontSize: '0.9rem' }}>
              {article?.title || article?.url || 'Article'}
            </Typography>
            <Typography variant="caption" color="text.secondary">{article?.source}</Typography>
          </Box>
          <IconButton size="small" onClick={onClose} sx={{ color: 'text.secondary', mt: -0.5 }}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>

        {/* tabs */}
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          sx={{
            px: 2, borderBottom: '1px solid rgba(100,136,175,0.15)',
            '& .MuiTab-root': { fontSize: '0.75rem', textTransform: 'none', minHeight: 40, py: 0 },
          }}
        >
          <Tab label="Article" />
          <Tab label="Processing" />
          <Tab label="Results" disabled={article?.pipeline_status !== 'completed'} />
        </Tabs>

        {/* content */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', px: 2.5, py: 2 }}>
          {article && tab === 0 && <ArticleTab articleId={article.article_id} />}
          {tab === 1 && <ProcessingTab run={run} />}
          {article && tab === 2 && article.pipeline_status === 'completed' && <ResultsTab articleId={article.article_id} />}
        </Box>
      </Box>
    </Drawer>
  )
}
