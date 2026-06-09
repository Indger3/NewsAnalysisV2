import { Typography, Skeleton, Alert, Stack, Divider } from '@mui/material'
import SectionCard from './SectionCard'

function MetaRow({ label, value }) {
  return (
    <Stack direction="row" spacing={2} sx={{ py: 0.875 }}>
      <Typography variant="body2" sx={{ minWidth: 88, fontWeight: 600, color: 'text.secondary', flexShrink: 0 }}>
        {label}
      </Typography>
      <Typography variant="body2" color="text.primary">{value}</Typography>
    </Stack>
  )
}

export default function MetadataCard({ loading, data, error }) {
  return (
    <SectionCard title="Metadata" accent="#7c3aed">
      {loading && (
        <Stack spacing={0.75}>
          {[72, 55, 65, 48, 60].map((w, i) => (
            <Skeleton key={i} variant="text" width={`${w}%`} sx={{ fontSize: '0.875rem' }} />
          ))}
        </Stack>
      )}
      {!loading && error && (
        <Alert severity="info" sx={{ py: 0.5 }}>Not yet available</Alert>
      )}
      {!loading && data && (
        <Stack divider={<Divider flexItem />}>
          {data.author && (
  <MetaRow
    label="Author"
    value={data.author}
  />
)}

{data.reporter && (
  <MetaRow
    label="Reporter"
    value={data.reporter}
  />
)}

{data.location && (
  <MetaRow
    label="Location"
    value={data.location}
  />
)}

{data.news_agency && (
  <MetaRow
    label="News Agency"
    value={data.news_agency}
  />
)}

{data.publisher && (
  <MetaRow
    label="Publisher"
    value={data.publisher}
  />
)}

{data.publication_date && (
  <MetaRow
    label="Publication Date"
    value={data.publication_date}
  />
)}
        </Stack>
      )}
      {!loading && !error && !data && (
        <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
          Submit an article to extract metadata.
        </Typography>
      )}
    </SectionCard>
  )
}
