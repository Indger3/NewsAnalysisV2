import {
  Box,
  Chip,
  CircularProgress,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material'
import ArticleIcon from '@mui/icons-material/Article'
import TimelineIcon from '@mui/icons-material/Timeline'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'

const STATUS_CHIP = {
  pending:   { label: 'Pending',    color: 'default' },
  running:   { label: 'Running',    color: 'primary' },
  completed: { label: 'Completed',  color: 'success' },
  failed:    { label: 'Failed',     color: 'error'   },
}

function relativeTime(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1)  return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

function StatusChip({ status }) {
  const cfg = STATUS_CHIP[status] ?? { label: status, color: 'default' }
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
      {status === 'running' && <CircularProgress size={12} thickness={5} />}
      <Chip label={cfg.label} color={cfg.color} size="small" variant="outlined" />
    </Box>
  )
}

export default function ArticleStatusTable({ articles, triggeringIds, onTrigger, onOpen }) {
  const cellSx = { py: 1, px: 1.5, fontSize: '0.78rem', borderColor: 'rgba(255,255,255,0.06)' }
  const headSx = { ...cellSx, color: 'rgba(255,255,255,0.45)', fontWeight: 600, fontSize: '0.7rem', letterSpacing: 0.5 }

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={headSx}>TITLE / URL</TableCell>
            <TableCell sx={headSx}>SOURCE</TableCell>
            <TableCell sx={{ ...headSx, textAlign: 'right' }}>WORDS</TableCell>
            <TableCell sx={headSx}>INGESTED</TableCell>
            <TableCell sx={headSx}>STATUS</TableCell>
            <TableCell sx={{ ...headSx, textAlign: 'center' }}>ACTIONS</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {articles.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} sx={{ ...cellSx, textAlign: 'center', color: 'text.disabled', py: 4 }}>
                No articles in database.
              </TableCell>
            </TableRow>
          )}
          {articles.map((a) => {
            const status = a.pipeline_status
            const isTriggering = triggeringIds.has(a.article_id)
            const canTrigger = !isTriggering && status !== 'running'
            const hasResults = status === 'completed'
            const hasRun = !!a.latest_run

            return (
              <TableRow
                key={a.article_id}
                sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' } }}
              >
                <TableCell sx={cellSx}>
                  <Tooltip title={a.url} placement="top" arrow>
                    <Typography noWrap sx={{ fontSize: '0.78rem', maxWidth: 260, color: 'text.primary' }}>
                      {a.title || a.url}
                    </Typography>
                  </Tooltip>
                </TableCell>

                <TableCell sx={{ ...cellSx, color: 'text.secondary' }}>
                  {a.source}
                </TableCell>

                <TableCell sx={{ ...cellSx, textAlign: 'right', color: 'text.secondary' }}>
                  {a.word_count?.toLocaleString() ?? '—'}
                </TableCell>

                <TableCell sx={{ ...cellSx, color: 'text.secondary', whiteSpace: 'nowrap' }}>
                  {relativeTime(a.ingested_at)}
                </TableCell>

                <TableCell sx={cellSx}>
                  <StatusChip status={status} />
                </TableCell>

                <TableCell sx={{ ...cellSx, textAlign: 'center', whiteSpace: 'nowrap' }}>
                  <Tooltip title="View article">
                    <span>
                      <IconButton size="small" onClick={() => onOpen(a, 'article')}
                        sx={{ color: 'rgba(255,255,255,0.5)', '&:hover': { color: '#fff' } }}>
                        <ArticleIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>

                  <Tooltip title="Processing state">
                    <span>
                      <IconButton size="small" disabled={!hasRun}
                        onClick={() => onOpen(a, 'processing')}
                        sx={{ color: hasRun ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.15)', '&:hover': { color: '#fff' } }}>
                        <TimelineIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>

                  <Tooltip title="Results">
                    <span>
                      <IconButton size="small" disabled={!hasResults}
                        onClick={() => onOpen(a, 'results')}
                        sx={{ color: hasResults ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.15)', '&:hover': { color: '#fff' } }}>
                        <AnalyticsIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>

                  <Tooltip title={canTrigger ? (status === 'pending' ? 'Run pipeline' : 'Re-run pipeline') : 'Pipeline running'}>
                    <span>
                      <IconButton size="small" disabled={!canTrigger}
                        onClick={() => onTrigger(a.article_id)}
                        sx={{ color: canTrigger ? '#60a5fa' : 'rgba(255,255,255,0.15)', '&:hover': { color: '#93c5fd' } }}>
                        {isTriggering
                          ? <CircularProgress size={14} thickness={5} />
                          : <PlayArrowIcon fontSize="small" />}
                      </IconButton>
                    </span>
                  </Tooltip>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
