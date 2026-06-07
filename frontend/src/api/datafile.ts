import http from '@/api/http'
import type { Paginated } from '@/api/types'

export interface DataFile {
  id: number
  folder: number | null
  folder_name: string | null
  name: string
  dataset: number | null
  dataset_name: string | null
  status: string
  row_count: number | null
  file_size: number | null
  error_msg: string
  created_at: string
}

export function listDataFiles(params: { dataset?: number; folder?: number; page?: number } = {}) {
  return http.get<Paginated<DataFile>>('/datafiles/', { params })
}

export async function downloadDataFile(id: number, filename: string) {
  const resp = await http.get(`/datafiles/${id}/download/`, { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
