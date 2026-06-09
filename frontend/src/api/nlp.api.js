import { post } from './rest_client'

const analyze = (endpoint) => (text, options = {}) => post(endpoint, { text, ...options })

export const analyzeEntities      = analyze('/v1/entities')
export const analyzeSummary       = analyze('/v1/summarize')
export const analyzeMetadata      = analyze('/v1/metadata')
export const analyzeTaxonomy      = analyze('/v1/taxonomy')
export const analyzeRelationships = analyze('/v1/relations')
export const analyzeNormalization = analyze('/v1/normalize')
export const analyzeBatch = (file) => {
  const formData = new FormData()

  formData.append('file', file)

  return post(
    '/v1/batch-analysis',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
}