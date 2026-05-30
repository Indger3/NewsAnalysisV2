import { Typography, Skeleton, Alert } from '@mui/material'
import SectionCard from './SectionCard'

export default function SummaryCard({ loading, data, error }) {
  return (
    <SectionCard title="Summary" accent="#2563eb">
      {loading && (
        <>
          <Skeleton variant="text" sx={{ fontSize: '0.875rem' }} />
          <Skeleton variant="text" width="92%" sx={{ fontSize: '0.875rem' }} />
          <Skeleton variant="text" width="78%" sx={{ fontSize: '0.875rem' }} />
        </>
      )}
      {!loading && error && (
        <Alert severity="info" sx={{ py: 0.5 }}>Not yet available</Alert>
      )}
      {!loading && data && (
        <Typography variant="body2" color="text.primary">
          {data.summary}
        </Typography>
      )}
      {!loading && !error && !data && (
        <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
          Submit an article to generate a summary.
        </Typography>
      )}
    </SectionCard>
  )
}
