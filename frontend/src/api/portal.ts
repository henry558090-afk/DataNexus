import http from '@/api/http'

export interface PortalFolder {
  id: number
  name: string
  children: PortalFolder[]
}

export interface PortalFile {
  id: number
  name: string
  row_count: number | null
  file_size: number | null
  created_at: string
  folder_id: number
}

export function getTree() {
  return http.get<PortalFolder[]>('/portal/tree/')
}

export function getFolderFiles(folderId: number) {
  return http.get<PortalFile[]>(`/portal/folders/${folderId}/files/`)
}

export function searchFiles(q: string, from?: string, to?: string) {
  return http.get<PortalFile[]>('/portal/search/', { params: { q, from, to } })
}

export async function downloadFile(id: number, filename: string, columns?: string[]) {
  const params = columns?.length ? { columns: columns.join(',') } : undefined
  const resp = await http.get(`/portal/files/${id}/download/`, { responseType: 'blob', params })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// ---- v0.24 ----
export interface PreviewData {
  columns: string[]
  rows: unknown[][]
}
export function previewFile(id: number, limit = 50) {
  return http.get<PreviewData>(`/portal/files/${id}/preview/`, { params: { limit } })
}
export function listFavorites() {
  return http.get<{ folder_id: number; name: string }[]>('/portal/favorites/')
}
export function toggleFavorite(folderId: number) {
  return http.post<{ favorited: boolean }>(`/portal/folders/${folderId}/favorite/`)
}
export function recentDownloads() {
  return http.get<{ target: string; created_at: string }[]>('/portal/recent-downloads/')
}
export function getUpdates(since?: string) {
  return http.get<{ count: number; files: PortalFile[] }>('/portal/updates/', { params: { since } })
}

// v0.25 用户提交访问申请 / 看自己的申请
export function myAccessRequests() {
  return http.get('/portal/access-requests/')
}
export function requestAccess(folderId: number, reason?: string) {
  return http.post('/portal/access-requests/', { folder: folderId, reason })
}
// 可申请的目录（标记为 requestable 且当前看不到的）
export function requestableFolders() {
  return http.get<{ id: number; name: string; pending: boolean }[]>(
    '/portal/requestable-folders/',
  )
}
