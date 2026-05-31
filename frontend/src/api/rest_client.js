import axios from 'axios'
import settings from '../settings'

const client = axios.create({
  baseURL: settings.apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(settings.tokenKey)
  if (token) config.headers.Authorization = `${settings.tokenType} ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(settings.tokenKey)
      localStorage.removeItem(settings.userKey)
      window.location.replace('/login')
    }
    return Promise.reject(err)
  }
)

export const get = (url, config)       => client.get(url, config)
export const post = (url, data, config) => client.post(url, data, config)
export const put = (url, data, config)  => client.put(url, data, config)
export const del = (url, config)       => client.delete(url, config)
