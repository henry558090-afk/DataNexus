import http from '@/api/http'
import type { Paginated } from '@/api/types'

export interface Execution {
  id: number
  dataset: number
  dataset_name: string
  status: string
  row_count: number | null
  file_size: number | null
  started_at: string
  ended_at: string | null
  error_msg: string
  is_latest: boolean
}

export function listExecutions(params: { dataset?: number; page?: number } = {}) {
  return http.get<Paginated<Execution>>('/executions/', { params })
}

// 带 Token 拉取 blob 再触发下载（anchor 无法带鉴权头）
export async function downloadExecution(id: number, filename: string) {
  const resp = await http.get(`/executions/${id}/download/`, { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
