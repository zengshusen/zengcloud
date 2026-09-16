import api from './http'
import type { AuthResponse, UserInfo } from '@/types/auth'

export function loginApi(username: string, password: string) {
  return api.post<AuthResponse>('/auth/login/', { username, password })
}

export function fetchMeApi() {
  return api.get<UserInfo>('/auth/me/')
}

export function logoutApi() {
  return api.post('/auth/logout/')
}
