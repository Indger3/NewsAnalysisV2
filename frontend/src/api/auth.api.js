import { post } from './rest_client'

export const login = (username, password) =>
  post('/v1/auth/login', { username, password })
