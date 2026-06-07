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

export function searchFiles(q: string) {
  return http.get<PortalFile[]>('/portal/search/', { params: { q } })
}

export async function downloadFile(id: number, filename: string) {
  const resp = await http.get(`/portal/files/${id}/download/`, { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
