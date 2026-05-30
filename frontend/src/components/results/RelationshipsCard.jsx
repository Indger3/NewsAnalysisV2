import { Typography, Skeleton, Alert, Stack, Chip } from '@mui/material'
import SectionCard from './SectionCard'

export default function RelationshipsCard({ loading, data, error }) {
  return (
    <SectionCard title="Relationships" accent="#d97706">
      {loading && (
        <Stack spacing={1}>
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rounded" height={32} sx={{ borderRadius: '8px' }} />
          ))}
        </Stack>
      )}
      {!loading && error && (
        <Alert severity="info" sx={{ py: 0.5 }}>Not yet available</Alert>
      )}
      {!loading && data && data.relationships?.length > 0 && (
        <Stack spacing={1.25}>
          {data.relationships.map(({ subj, verb, obj }, i) => (
            <Stack key={i} direction="row" alignItems="center" gap={1} flexWrap="wrap">
              <Chip
                label={subj}
                size="small"
                sx={{ bgcolor: '#dbeafe', color: '#1d4ed8', border: '1px solid #93c5fd' }}
              />
              <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', fontStyle: 'italic', mx: 0.25 }}>
                → {verb} →
              </Typography>
              <Chip
                label={obj}
                size="small"
                sx={{ bgcolor: '#ede9fe', color: '#5b21b6', border: '1px solid #c4b5fd' }}
              />
            </Stack>
          ))}
        </Stack>
      )}
      {!loading && !error && !data && (
        <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
          Submit an article to detect relationships.
        </Typography>
      )}
    </SectionCard>
  )
}
