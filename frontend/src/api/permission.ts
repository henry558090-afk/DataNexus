import http from '@/api/http'

export interface PlatformUser {
  id: number
  username: string
  is_superuser: boolean
  is_assistant_admin: boolean
  is_boss: boolean
  is_active: boolean
}

export interface UserInput {
  username?: string
  password?: string
  is_assistant_admin?: boolean
  is_boss?: boolean
  is_active?: boolean
}

export function listUsers() {
  return http.get<PlatformUser[]>('/users/')
}
export function createUser(data: UserInput) {
  return http.post<PlatformUser>('/users/', data)
}
export function updateUser(id: number, data: UserInput) {
  return http.patch<PlatformUser>(`/users/${id}/`, data)
}
export function deleteUser(id: number) {
  return http.delete(`/users/${id}/`)
}

export interface Membership {
  id: number
  user: number
  username: string
  department: number
  department_name: string
}

export function listMemberships(userId: number) {
  return http.get<Membership[]>('/memberships/', { params: { user: userId } })
}
export function createMembership(data: { user: number; department: number }) {
  return http.post<Membership>('/memberships/', data)
}
export function deleteMembership(id: number) {
  return http.delete(`/memberships/${id}/`)
}
