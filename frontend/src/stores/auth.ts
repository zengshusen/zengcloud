import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { fetchMeApi, loginApi, logoutApi } from '@/api/auth'
import type { UserInfo } from '@/types/auth'

const ACCESS_KEY = 'zc_access'
const REFRESH_KEY = 'zc_refresh'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem(ACCESS_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_KEY))
  const user = ref<UserInfo | null>(null)
  const bootstrapped = ref(false)

  const isAuthenticated = computed(() => Boolean(accessToken.value))

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem(ACCESS_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
  }

  function clear() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  }

  async function login(username: string, password: string) {
    const { data } = await loginApi(username, password)
    setTokens(data.access, data.refresh)
    user.value = data.user
    return data.user
  }

  async function fetchMe() {
    if (!accessToken.value) {
      bootstrapped.value = true
      return null
    }
    try {
      const { data } = await fetchMeApi()
      user.value = data
      return data
    } catch {
      clear()
      return null
    } finally {
      bootstrapped.value = true
    }
  }

  async function logout() {
    try {
      if (accessToken.value) {
        await logoutApi()
      }
    } catch {
      // ignore network errors on logout
    } finally {
      clear()
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    bootstrapped,
    isAuthenticated,
    setTokens,
    clear,
    login,
    fetchMe,
    logout,
  }
})
