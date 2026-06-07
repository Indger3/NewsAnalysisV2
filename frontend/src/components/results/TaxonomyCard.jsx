// import { Typography, Skeleton, Alert, Chip, Box } from '@mui/material'
// import SectionCard from './SectionCard'

// const chipRowSx = { display: 'flex', flexWrap: 'wrap', gap: 1 }

// export default function TaxonomyCard({ loading, data, error }) {
//   return (
//     <SectionCard title="Taxonomy" accent="#0891b2">
//       {loading && (
//         <Box sx={chipRowSx}>
//           {[72, 96, 58, 112, 80].map((w, i) => (
//             <Skeleton key={i} variant="rounded" width={w} height={26} sx={{ borderRadius: '6px' }} />
//           ))}
//         </Box>
//       )}
//       {!loading && error && (
//         <Alert severity="info" sx={{ py: 0.5 }}>Not yet available</Alert>
//       )}
//       {!loading && data && data.categories?.length > 0 && (
//         <Box sx={chipRowSx}>
//           {data.categories.map((cat) => (
//             <Chip
//               key={cat}
//               label={cat}
//               size="small"
//               sx={{
//                 bgcolor: '#e0f2fe',
//                 color: '#075985',
//                 border: '1px solid #bae6fd',
//                 '&:hover': { bgcolor: '#bae6fd' },
//               }}
//             />
//           ))}
//         </Box>
//       )}
//       {!loading && !error && !data && (
//         <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
//           Submit an article to classify taxonomy.
//         </Typography>
//       )}
//     </SectionCard>
//   )
// }
import { Typography, Skeleton, Alert, Box, Chip } from '@mui/material'
import SectionCard from './SectionCard'

export default function TaxonomyCard({ loading, data, error }) {
  return (
    <SectionCard title="Taxonomy" accent="#0891b2">
      {loading && <Skeleton variant="rounded" height={80} />}

      {!loading && error && (
        <Alert severity="error">
          Failed to classify article
        </Alert>
      )}

      {!loading && data && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Chip
            label={`Topic: ${data.topic}`}
            color="primary"
          />

          <Chip
            label={`Subtopic: ${data.subtopic}`}
            color="secondary"
          />

          <Typography variant="caption">
            Topic Confidence: {(data.topic_confidence * 100).toFixed(1)}%
          </Typography>

          <Typography variant="caption">
            Subtopic Confidence: {(data.subtopic_confidence * 100).toFixed(1)}%
          </Typography>
        </Box>
      )}

      {!loading && !error && !data && (
        <Typography
          variant="body2"
          color="text.disabled"
          sx={{ fontStyle: 'italic' }}
        >
          Submit an article to classify taxonomy.
        </Typography>
      )}
    </SectionCard>
  )
}