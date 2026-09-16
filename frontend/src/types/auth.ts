export interface UserInfo {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
}

export interface AuthResponse {
  access: string
  refresh: string
  user: UserInfo
}
