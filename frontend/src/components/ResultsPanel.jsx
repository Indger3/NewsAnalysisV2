import { Box, Typography, Stack, Button } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import { downloadAnalysis } from '../utils/download'
import SummaryCard from './results/SummaryCard'
import MetadataCard from './results/MetadataCard'
import TaxonomyCard from './results/TaxonomyCard'
import EntitiesCard from './results/EntitiesCard'
import RelationshipsCard from './results/RelationshipsCard'
import NormalizationCard from './results/NormalizationCard'


export default function ResultsPanel({ loading, results, errors ,articleText,}) {
  const canDownload =
  !Object.values(loading).some(Boolean) &&
  results.summary &&
  results.metadata &&
  results.taxonomy &&
  results.entities &&
  results.relationships &&
  results.normalization;
console.log("Results in ResultsPanel:", results);
console.log("Metadata in ResultsPanel:", results.metadata);
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
        display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
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
        <Button
    size="small"
    variant="contained"
    startIcon={<DownloadIcon />}
    disabled={!canDownload}
    onClick={() => downloadAnalysis(articleText, results)}
  >
    Download JSON
  </Button>
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

          <NormalizationCard
            loading={loading.normalization}
            data={results.normalization}
            error={errors.normalization}
          />
        </Stack>
      </Box>
    </Box>
  )
}
