import { Typography, Skeleton, Alert, Stack, Chip } from '@mui/material'
import SectionCard from './SectionCard'

export default function TaxonomyCard({ loading, data, error }) {
  return (
    <SectionCard title="Taxonomy" accent="#0891b2">
      {loading && (
        <Stack direction="row" flexWrap="wrap" gap={1}>
          {[72, 96, 58, 112, 80].map((w, i) => (
            <Skeleton key={i} variant="rounded" width={w} height={26} sx={{ borderRadius: '6px' }} />
          ))}
        </Stack>
      )}
      {!loading && error && (
        <Alert severity="info" sx={{ py: 0.5 }}>Not yet available</Alert>
      )}
      {!loading && data && data.categories?.length > 0 && (
        <Stack direction="row" flexWrap="wrap" gap={1}>
          {data.categories.map((cat) => (
            <Chip
              key={cat}
              label={cat}
              size="small"
              sx={{
                bgcolor: '#e0f2fe',
                color: '#075985',
                border: '1px solid #bae6fd',
                '&:hover': { bgcolor: '#bae6fd' },
              }}
            />
          ))}
        </Stack>
      )}
      {!loading && !error && !data && (
        <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
          Submit an article to classify taxonomy.
        </Typography>
      )}
    </SectionCard>
  )
}
