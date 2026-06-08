// import { Typography, Skeleton, Alert, Stack, Chip } from '@mui/material'
// import { useRef, useEffect } from 'react'
// import SectionCard from './SectionCard'
// import ForceGraph2D from 'react-force-graph-2d'
// export default function RelationshipsCard({ loading, data, error }) {
// const graphData = data?.graph

//     ? {

//         nodes: data.graph.nodes,

//         links: data.graph.edges.map(edge => ({

//           source: edge.from,

//           target: edge.to,

//           label: edge.label

//         }))

//       }

//     : null


// const fgRef = useRef()

// useEffect(() => {
//   if (!fgRef.current || !graphData) return

//   fgRef.current.d3Force('link').distance(120)

//   fgRef.current.d3Force('charge').strength(-300)

// }, [graphData])

//   return (
//     <SectionCard title="Relationships" accent="#d97706">
//       {loading && (
//         <Stack spacing={1}>
//           {[1, 2, 3].map((i) => (
//             <Skeleton key={i} variant="rounded" height={32} sx={{ borderRadius: '8px' }} />
//           ))}
//         </Stack>
//       )}
//       {!loading && error && (
//         <Alert severity="info" sx={{ py: 0.5 }}>Not yet available</Alert>
//       )}
//       {!loading && data && data.relationships?.length > 0 && (
//         <Stack spacing={1.25}>
//           {data.relationships.map(({ subj, verb, obj }, i) => (
//             <Stack key={i} direction="row" alignItems="center" gap={1} flexWrap="wrap">
//               <Chip
//                 label={subj}
//                 size="small"
//                 sx={{ bgcolor: '#dbeafe', color: '#1d4ed8', border: '1px solid #93c5fd' }}
//               />
//               <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', fontStyle: 'italic', mx: 0.25 }}>
//                 → {verb} →
//               </Typography>
//               <Chip
//                 label={obj}
//                 size="small"
//                 sx={{ bgcolor: '#ede9fe', color: '#5b21b6', border: '1px solid #c4b5fd' }}
//               />
//             </Stack>
//           ))}
//           {graphData && graphData.nodes.length > 0 && (

//   <>

//     <Typography

//       variant="subtitle2"

//       sx={{

//         mt: 3,

//         mb: 1,

//         fontWeight: 600

//       }}

//     >

//       Knowledge Graph

//     </Typography>

//     <div

//       style={{

//         height: '400px',

//         border: '1px solid #e5e7eb',

//         borderRadius: '12px',

//         overflow: 'hidden'

//       }}

//     >
// <ForceGraph2D
//   ref={fgRef}

//   graphData={graphData}

//   onEngineStop={() => {

//     fgRef.current?.zoomToFit(400, 50)

//   }}
// width={1400}

// height={400}

// cooldownTicks={200}

// d3VelocityDecay={0.35}

// minZoom={0.6}

// maxZoom={5}
//   nodeLabel={(node) => node.id}

//   linkLabel={(link) => link.label}

//   nodeRelSize={8}

//   linkWidth={2.5}

//   linkColor={() => '#64748b'}

//   linkDirectionalArrowLength={8}

//   linkDirectionalArrowRelPos={1}

  

  

//   enableZoomInteraction

//   enablePanInteraction

//   enableNodeDrag

  

 
//   onNodeHover={(node) => {
//     document.body.style.cursor = node ? 'pointer' : 'default'
//   }}

//   nodeCanvasObject={(node, ctx, globalScale) => {
//     const label = node.id

//     const fontSize = Math.max(12, 14 / globalScale)

//     ctx.font = `${fontSize}px Sans-Serif`

//     const textWidth = ctx.measureText(label).width

//     ctx.beginPath()
//     ctx.arc(node.x, node.y, 10, 0, 2 * Math.PI)
//     ctx.fillStyle = '#2563eb'
//     ctx.fill()

//     ctx.fillStyle = 'rgba(255,255,255,0.95)'
//     ctx.fillRect(
//       node.x + 12,
//       node.y - fontSize,
//       textWidth + 10,
//       fontSize + 6
//     )

//     ctx.fillStyle = '#111827'
//     ctx.fillText(
//       label,
//       node.x + 16,
//       node.y + 4
//     )
//   }}

//   linkCanvasObjectMode={() => 'after'}

//   linkCanvasObject={(link, ctx) => {
//     const start = link.source
//     const end = link.target

//     if (
//       typeof start !== 'object' ||
//       typeof end !== 'object'
//     ) return

//     const label = link.label || ''

//     const midX = (start.x + end.x) / 2
//     const midY = (start.y + end.y) / 2

//     ctx.font = 'bold 12px Sans-Serif'

//     const textWidth = ctx.measureText(label).width

//     ctx.fillStyle = 'rgba(255,255,255,0.98)'
//     ctx.fillRect(
//       midX - textWidth / 2 - 6,
//       midY - 10,
//       textWidth + 12,
//       18
//     )

//     ctx.fillStyle = '#dc2626'
//     ctx.fillText(
//       label,
//       midX - textWidth / 2,
//       midY + 3
//     )
//   }}
// />

//     </div>

//   </>

// )}
//         </Stack>
//       )}
//       {!loading && !error && !data && (
//         <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
//           Submit an article to detect relationships.
//         </Typography>
//       )}
//     </SectionCard>
//   )
// }

import dagre from 'dagre'
import { Typography, Skeleton, Alert, Stack, Chip } from '@mui/material'
import { useRef, useEffect } from 'react'
import SectionCard from './SectionCard'
import ReactFlow, {

  Background,

  Controls,

  MiniMap,
  MarkerType

} from 'reactflow'

import 'reactflow/dist/style.css'
export default function RelationshipsCard({ loading, data, error }) {
const graphData = data?.graph

    ? {

        nodes: data.graph.nodes,

        links: data.graph.edges.map(edge => ({

          source: edge.from.trim(),

          target: edge.to.trim(),

          label: edge.label.trim()

        }))

      }

    : null

if (graphData) {

  console.log("NODES", graphData.nodes)

  console.log("LINKS", graphData.links)

}
// const nodes = []

// const edges = []

// const nodeMap = new Map()

// let currentX = 0

// let currentY = 0

// graphData?.nodes?.forEach((node, index) => {

//   nodeMap.set(node.id, true)

//   nodes.push({

//     id: node.id,

//     data: {

//       label: node.id

//     },

//     position: {

//       x: currentX,

//       y: currentY

//     }

//   })

//   currentX += 250

//   if (currentX > 1000) {

//     currentX = 0

//     currentY += 150

//   }

// })
//commentout to remove dagre
const nodes = []

const edges = []

const dagreGraph = new dagre.graphlib.Graph()

dagreGraph.setDefaultEdgeLabel(() => ({}))

dagreGraph.setGraph({
  rankdir: 'LR',
  nodesep: 80,
  ranksep: 180
})

graphData?.nodes?.forEach((node) => {

  dagreGraph.setNode(node.id, {
    width: 180,
    height: 50
  })

})
//-----------------
graphData?.links?.forEach((link, index) => {
  console.log(link)
  console.log(

  "EDGE:",

  link.source,

  "--",

  link.label,

  "-->",

  link.target

)
dagreGraph.setEdge(link.source, link.target) //commentout to remove dagre

  edges.push({

    id: `e${index}`,

    source: link.source,

    target: link.target,

    type: 'smoothstep',

    label: link.label,

    animated: true,

    markerEnd: {

    type: MarkerType.ArrowClosed

  }

  })

})
//commentout to remove dagre
dagre.layout(dagreGraph)

graphData?.nodes?.forEach((node) => {

  const pos = dagreGraph.node(node.id)

  nodes.push({

    id: node.id,

    data: {
      label: node.id
    },

    position: {
      x: pos.x,
      y: pos.y
    },

    style: {
      width: 180,
      borderRadius: '8px'
    }

  })

})
//----------------
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
<div
  style={{
    height: '400px',
    border: '1px solid #e5e7eb',
    borderRadius: '12px'
  }}
>
  <ReactFlow
    nodes={nodes}
    edges={edges}
    fitView
  >
    <MiniMap />
    <Controls />
    <Background />
  </ReactFlow>
</div>

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
