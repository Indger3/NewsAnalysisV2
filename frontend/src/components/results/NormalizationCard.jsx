import {
  Typography,
  Skeleton,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Box,
} from '@mui/material'

import SectionCard from './SectionCard'

export default function NormalizationCard({
  loading,
  data,
  error,
}) {
  const mappings = data?.normalized_entities || {}

  return (
    <SectionCard
      title="Entity Normalization"
      accent="#7c3aed"
    >
      {loading && (
        <>
          <Skeleton height={32} />
          <Skeleton height={32} />
          <Skeleton height={32} />
        </>
      )}

      {!loading && error && (
        <Alert severity="error">
          Failed to normalize entities.
        </Alert>
      )}

      {!loading &&
        !error &&
        Object.keys(mappings).length > 0 && (
          <Box sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>
                    <strong>Mention</strong>
                  </TableCell>

                  <TableCell>
                    <strong>Canonical Entity</strong>
                  </TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {Object.entries(mappings).map(
                  ([mention, canonical]) => (
                    <TableRow key={mention}>
                      <TableCell>
                        {mention}
                      </TableCell>

                      <TableCell>
                        {canonical}
                      </TableCell>
                    </TableRow>
                  )
                )}
              </TableBody>
            </Table>
          </Box>
        )}

      {!loading &&
        !error &&
        !Object.keys(mappings).length && (
          <Typography
            variant="body2"
            color="text.disabled"
            sx={{ fontStyle: 'italic' }}
          >
            Submit an article to normalize entities.
          </Typography>
        )}
    </SectionCard>
  )
}