import { Typography, Skeleton, Alert, Stack, Chip, Box } from '@mui/material'
import SectionCard from './SectionCard'

const ENTITY_STYLES = {
  PERSON:  { bg: '#ede9fe', color: '#5b21b6', border: '#c4b5fd' },
  ORG:     { bg: '#dbeafe', color: '#1d4ed8', border: '#93c5fd' },
  GPE:     { bg: '#d1fae5', color: '#065f46', border: '#6ee7b7' },
  LOC:     { bg: '#d1fae5', color: '#065f46', border: '#6ee7b7' },
  DATE:    { bg: '#fef3c7', color: '#92400e', border: '#fcd34d' },
  TIME:    { bg: '#fef3c7', color: '#92400e', border: '#fcd34d' },
  MONEY:   { bg: '#fee2e2', color: '#991b1b', border: '#fca5a5' },
  PERCENT: { bg: '#fee2e2', color: '#991b1b', border: '#fca5a5' },
  PRODUCT: { bg: '#e0f2fe', color: '#075985', border: '#7dd3fc' },
  EVENT:   { bg: '#fce7f3', color: '#9d174d', border: '#f9a8d4' },
}

const defaultStyle = { bg: '#f1f5f9', color: '#475569', border: '#cbd5e1' }

export default function EntitiesCard({ loading, data, error }) {
  const grouped = {}
  if (data?.entities) {
    for (const { entity, label } of data.entities) {
      if (!grouped[label]) grouped[label] = []
      grouped[label].push(entity)
    }
  }

  return (
    <SectionCard title="Entities" accent="#059669">
      {loading && (
        <Stack spacing={2}>
          {[1, 2].map((g) => (
            <Box key={g}>
              <Skeleton variant="rounded" width={52} height={20} sx={{ mb: 0.75, borderRadius: '4px' }} />
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                {[80, 104, 68].map((w, i) => (
                  <Skeleton key={i} variant="rounded" width={w} height={24} sx={{ borderRadius: '6px' }} />
                ))}
              </Box>
            </Box>
          ))}
        </Stack>
      )}
      {!loading && error && (
        <Alert severity="error" sx={{ py: 0.5 }}>Failed to extract entities.</Alert>
      )}
      {!loading && data && Object.keys(grouped).length > 0 && (
        <Stack spacing={2}>
          {Object.entries(grouped).map(([label, items]) => {
            const style = ENTITY_STYLES[label] ?? defaultStyle
            return (
              <Box key={label}>
                <Box sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  px: 0.75,
                  py: 0.25,
                  mb: 0.75,
                  borderRadius: '4px',
                  bgcolor: style.bg,
                  border: `1px solid ${style.border}`,
                }}>
                  <Typography sx={{ fontSize: '0.62rem', fontWeight: 800, letterSpacing: 0.8, color: style.color, lineHeight: 1 }}>
                    {label}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                  {items.map((item) => (
                    <Chip
                      key={item}
                      label={item}
                      size="small"
                      sx={{
                        bgcolor: style.bg,
                        color: style.color,
                        border: `1px solid ${style.border}`,
                        '&:hover': { opacity: 0.85 },
                      }}
                    />
                  ))}
                </Box>
              </Box>
            )
          })}
        </Stack>
      )}
      {!loading && !error && !data && (
        <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
          Submit an article to extract named entities.
        </Typography>
      )}
    </SectionCard>
  )
}
