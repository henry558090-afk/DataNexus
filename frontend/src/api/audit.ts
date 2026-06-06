import http from '@/api/http'
import type { Paginated } from '@/api/types'

export interface AuditLog {
  id: number
  username: string
  action: string
  action_display: string
  target: string
  ip: string | null
  created_at: string
}

export function listAuditLogs(params: { action?: string; page?: number } = {}) {
  return http.get<Paginated<AuditLog>>('/audit-logs/', { params })
}
