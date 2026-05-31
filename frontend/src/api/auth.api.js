import { post } from './rest_client'

export const login  = (email, password) => post('/v1/auth/login', { email, password })
export const signup = (email, password, name) => post('/v1/auth/signup', { email, password, name })
