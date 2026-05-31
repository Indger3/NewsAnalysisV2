import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AppBar,
  Box,
  Button,
  CircularProgress,
  Toolbar,
  Typography,
} from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import settings from '../settings'
import { listArticles, triggerPipeline, getArticleStatus } from '../api/pipeline.api'
import ArticleStatusTable from '../components/pipeline/ArticleStatusTable'
import ArticleDetailDrawer from '../components/pipeline/ArticleDetailDrawer'

const POLL_INTERVAL_MS = 2500

export default function PipelinePage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [triggeringIds, setTriggeringIds] = useState(new Set())

  // polling: Set of article_ids currently being polled
  const pollingIds = useRef(new Set())
  const pollTimer = useRef(null)

  // statusMap: { [article_id]: latest_run_with_steps } — updated by polls
  const [statusMap, setStatusMap] = useState({})

  // drawer state
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerArticle, setDrawerArticle] = useState(null)
  const [drawerTab, setDrawerTab] = useState('article')

  // ---------------------------------------------------------------------------
  // Data loading
  // ---------------------------------------------------------------------------

  const fetchArticles = useCallback(async () => {
    try {
      const res = await listArticles()
      const list = res.data.articles
      setArticles(list)

      // seed statusMap from article list data
      setStatusMap((prev) => {
        const next = { ...prev }
        for (const a of list) {
          if (a.latest_run) next[a.article_id] = a.latest_run
        }
        return next
      })

      // start polling for any already-running articles
      for (const a of list) {
        if (a.pipeline_status === 'running') {
          pollingIds.current.add(a.article_id)
        }
      }
    } catch (err) {
      console.error('Failed to fetch articles', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchArticles()
  }, [fetchArticles])

  // ---------------------------------------------------------------------------
  // Polling loop
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const tick = async () => {
      if (pollingIds.current.size === 0) return

      for (const id of [...pollingIds.current]) {
        try {
          const res = await getArticleStatus(id)
          const { pipeline_status, latest_run } = res.data

          if (latest_run) {
            setStatusMap((prev) => ({ ...prev, [id]: latest_run }))
          }

          // update article row status in table
          setArticles((prev) =>
            prev.map((a) => (a.article_id === id ? { ...a, pipeline_status, latest_run } : a))
          )

          if (pipeline_status === 'completed' || pipeline_status === 'failed') {
            pollingIds.current.delete(id)
            setTriggeringIds((prev) => { const s = new Set(prev); s.delete(id); return s })
          }
        } catch (err) {
          console.error(`Poll failed for article ${id}`, err)
        }
      }
    }

    pollTimer.current = setInterval(tick, POLL_INTERVAL_MS)
    return () => clearInterval(pollTimer.current)
  }, [])

  // ---------------------------------------------------------------------------
  // Trigger
  // ---------------------------------------------------------------------------

  async function handleTrigger(articleId) {
    setTriggeringIds((prev) => new Set(prev).add(articleId))
    try {
      await triggerPipeline(articleId)
      setArticles((prev) =>
        prev.map((a) => (a.article_id === articleId ? { ...a, pipeline_status: 'running' } : a))
      )
      pollingIds.current.add(articleId)
    } catch (err) {
      console.error('Trigger failed', err)
      setTriggeringIds((prev) => { const s = new Set(prev); s.delete(articleId); return s })
    }
  }

  // ---------------------------------------------------------------------------
  // Drawer
  // ---------------------------------------------------------------------------

  function handleOpen(article, tab) {
    setDrawerArticle(article)
    setDrawerTab(tab)
    setDrawerOpen(true)
  }

  // keep drawer article in sync with live status updates
  const drawerRun = drawerArticle ? statusMap[drawerArticle.article_id] ?? drawerArticle.latest_run : null

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" color="default">
        <Toolbar sx={{ gap: 2 }}>
          <Box sx={{
            width: 28, height: 28, borderRadius: 1, bgcolor: 'primary.main',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <Typography sx={{ color: '#fff', fontWeight: 900, fontSize: '0.75rem', lineHeight: 1 }}>N</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5, flexGrow: 1 }}>
            <Typography sx={{ fontWeight: 800, letterSpacing: -0.5, color: 'primary.main', fontSize: '1rem' }}>
              {settings.appName}
            </Typography>
            <Typography sx={{ fontSize: '0.72rem', color: 'text.disabled', fontWeight: 500, letterSpacing: 0.2 }}>
              Pipeline
            </Typography>
          </Box>
          {user?.pages?.some((p) => p.slug === 'analysis') && (
            <Button
              size="small"
              onClick={() => navigate('/')}
              sx={{ color: 'text.secondary', fontSize: '0.75rem', textTransform: 'none', '&:hover': { color: 'text.primary' } }}
            >
              Ad-hoc Analysis
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

      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1rem' }}>
            Article Processing Pipeline
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Workflow-driven · DB-backed · Status auto-refreshes
          </Typography>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{
            bgcolor: 'background.paper',
            border: '1px solid #e2e8f0',
            borderRadius: 2,
            overflow: 'hidden',
            boxShadow: '0 1px 3px 0 rgba(0,0,0,0.06)',
          }}>
            <ArticleStatusTable
              articles={articles}
              triggeringIds={triggeringIds}
              onTrigger={handleTrigger}
              onOpen={handleOpen}
            />
          </Box>
        )}
      </Box>

      <ArticleDetailDrawer
        open={drawerOpen}
        article={drawerArticle}
        initialTab={drawerTab}
        run={drawerRun}
        onClose={() => setDrawerOpen(false)}
      />
    </Box>
  )
}
