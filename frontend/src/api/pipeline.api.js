import { get, post } from './rest_client'

export const listArticles      = ()   => get('/v1/pipeline/articles')
export const getArticle        = (id) => get(`/v1/pipeline/articles/${id}`)
export const triggerPipeline   = (id) => post(`/v1/pipeline/articles/${id}/trigger`)
export const getArticleStatus  = (id) => get(`/v1/pipeline/articles/${id}/status`)
export const getArticleResults = (id) => get(`/v1/pipeline/articles/${id}/results`)
