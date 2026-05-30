import { Box, Typography, Stack } from '@mui/material'
import SummaryCard from './results/SummaryCard'
import MetadataCard from './results/MetadataCard'
import TaxonomyCard from './results/TaxonomyCard'
import EntitiesCard from './results/EntitiesCard'
import RelationshipsCard from './results/RelationshipsCard'

export default function ResultsPanel({ loading, results, errors }) {
  return (
    <Box sx={{ width: '60%', height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
      <Box sx={{
        px: 3,
        py: 2,
        borderBottom: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
        position: 'sticky',
        top: 0,
        zIndex: 1,
        flexShrink: 0,
      }}>
        <Typography sx={{
          fontSize: '0.65rem',
          fontWeight: 800,
          letterSpacing: 1.8,
          textTransform: 'uppercase',
          color: 'text.secondary',
        }}>
          Analysis Results
        </Typography>
      </Box>

      <Box sx={{ overflowY: 'auto', flexGrow: 1, p: 3 }}>
        <Stack spacing={2}>
          <SummaryCard
            loading={loading.summary}
            data={results.summary}
            error={errors.summary}
          />
          <MetadataCard
            loading={loading.metadata}
            data={results.metadata}
            error={errors.metadata}
          />
          <TaxonomyCard
            loading={loading.taxonomy}
            data={results.taxonomy}
            error={errors.taxonomy}
          />
          <EntitiesCard
            loading={loading.entities}
            data={results.entities}
            error={errors.entities}
          />
          <RelationshipsCard
            loading={loading.relationships}
            data={results.relationships}
            error={errors.relationships}
          />
        </Stack>
      </Box>
    </Box>
  )
}
