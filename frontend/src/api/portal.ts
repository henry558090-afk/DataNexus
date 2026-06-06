import http from '@/api/http'

export interface PortalDataset {
  id: number
  name: string
  description: string
}

export interface PortalCategory {
  id: number
  name: string
  datasets: PortalDataset[]
}

export interface PortalDepartment {
  id: number
  name: string
  categories: PortalCategory[]
}

export interface PortalExecution {
  id: number
  status: string
  row_count: number | null
  file_size: number | null
  started_at: string
}

export interface PortalDetail {
  id: number
  name: string
  description: string
  executions: PortalExecution[]
}

export function getTree() {
  return http.get<PortalDepartment[]>('/portal/tree/')
}

export function getDatasetDetail(id: number) {
  return http.get<PortalDetail>(`/portal/datasets/${id}/`)
}

export async function downloadPortal(execId: number, filename: string) {
  const resp = await http.get(`/portal/executions/${execId}/download/`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
