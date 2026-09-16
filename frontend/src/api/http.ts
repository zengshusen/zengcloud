import type { InternalAxiosRequestConfig } from 'axios'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean }

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const auth = useAuthStore()
    const status = error.response?.status
    const original = error.config as RetryConfig | undefined

    if (status === 401 && auth.refreshToken && original && !original._retry) {
      original._retry = true
      try {
        const { data } = await axios.post('/api/auth/refresh/', {
          refresh: auth.refreshToken,
        })
        auth.setTokens(data.access, auth.refreshToken)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        auth.clear()
        if (router.currentRoute.value.name !== 'login') {
          await router.push({
            name: 'login',
            query: { redirect: router.currentRoute.value.fullPath },
          })
        }
      }
    }

    return Promise.reject(error)
  },
)

export default api
