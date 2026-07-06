import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath
} from 'reactflow'

export default function RelationshipEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd
}) {
  const offset = (data?.duplicateIndex || 0) * 40

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    curvature: 0.25 + offset / 200
  })

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
      />

      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY - offset}px)`,

            background: 'white',

            padding: '2px 6px',

            borderRadius: '4px',

            fontSize: '12px',

            fontWeight: 600,

            border: '1px solid #e5e7eb',

            pointerEvents: 'all',

            whiteSpace: 'nowrap'
          }}
        >
          {data?.label}
        </div>
      </EdgeLabelRenderer>
    </>
  )
}