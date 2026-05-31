import { Card, CardContent, Box, Typography } from '@mui/material'

export default function SectionCard({ title, accent, children }) {
  return (
    <Card sx={{ overflow: 'hidden' }}>
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 2 }}>
          <Box sx={{ width: 3, height: 15, borderRadius: '2px', bgcolor: accent, flexShrink: 0 }} />
          <Typography sx={{
            fontSize: '0.67rem',
            fontWeight: 800,
            letterSpacing: 1.6,
            textTransform: 'uppercase',
            color: 'text.secondary',
            lineHeight: 1,
          }}>
            {title}
          </Typography>
        </Box>
        {children}
      </CardContent>
    </Card>
  )
}
