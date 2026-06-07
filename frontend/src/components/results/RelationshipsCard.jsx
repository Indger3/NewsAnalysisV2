import { Typography, Skeleton, Alert, Stack, Chip } from '@mui/material'
import SectionCard from './SectionCard'
import ForceGraph2D from 'react-force-graph-2d'
export default function RelationshipsCard({ loading, data, error }) {
const graphData = data?.graph

    ? {

        nodes: data.graph.nodes,

        links: data.graph.edges.map(edge => ({

          source: edge.from,

          target: edge.to,

          label: edge.label

        }))

      }

    : null

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
          {graphData && graphData.nodes.length > 0 && (

  <>

    <Typography

      variant="subtitle2"

      sx={{

        mt: 3,

        mb: 1,

        fontWeight: 600

      }}

    >

      Knowledge Graph

    </Typography>

    <div

      style={{

        height: '400px',

        border: '1px solid #e5e7eb',

        borderRadius: '12px',

        overflow: 'hidden'

      }}

    >
<ForceGraph2D
  graphData={graphData}

  nodeLabel="id"

  linkWidth={2}
  linkColor={() => '#94a3b8'}

  cooldownTicks={100}

  d3VelocityDecay={0.4}

  nodeCanvasObject={(node, ctx, globalScale) => {
    const label = node.id

    const fontSize = Math.max(10, 14 / globalScale)

    ctx.font = `${fontSize}px Sans-Serif`

    const textWidth = ctx.measureText(label).width

    // Blue node
    ctx.fillStyle = '#2563eb'
    ctx.beginPath()
    ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI)
    ctx.fill()

    // White background behind entity name
    ctx.fillStyle = 'rgba(255,255,255,0.9)'
    ctx.fillRect(
      node.x + 10,
      node.y - fontSize,
      textWidth + 6,
      fontSize + 4
    )

    // Entity name
    ctx.fillStyle = '#111827'
    ctx.fillText(
      label,
      node.x + 13,
      node.y + 3
    )
  }}

  linkCanvasObjectMode={() => 'after'}

  linkCanvasObject={(link, ctx) => {
    const start = link.source
    const end = link.target

    if (
      typeof start !== 'object' ||
      typeof end !== 'object'
    ) return

    const label = link.label || ''

    const textPosX = (start.x + end.x) / 2
    const textPosY = (start.y + end.y) / 2

    ctx.font = '11px Sans-Serif'

    const textWidth = ctx.measureText(label).width

    // White box behind relation text
    ctx.fillStyle = 'rgba(255,255,255,0.95)'
    ctx.fillRect(
      textPosX - textWidth / 2 - 4,
      textPosY - 10,
      textWidth + 8,
      16
    )

    // Relation text
    ctx.fillStyle = '#dc2626'
    ctx.fillText(
      label,
      textPosX - textWidth / 2,
      textPosY + 2
    )
  }}
/>

    </div>

  </>

)}
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
