import http from '@/api/http'

export interface DatasetLatest {
  id: number
  status: string
  row_count: number | null
  file_size: number | null
  started_at: string
}

export interface Dataset {
  id: number
  name: string
  description: string
  category: number | null
  datasource: number
  datasource_name: string
  sql_text: string
  is_active: boolean
  created_at: string
  updated_at: string
  latest: DatasetLatest | null
}

export interface DatasetInput {
  name: string
  description?: string
  datasource: number | null
  sql_text: string
}

export interface PreviewResult {
  ok: boolean
  message?: string
  columns?: string[]
  rows?: unknown[][]
}

export interface ExecutionResult {
  id: number
  status: string
  row_count: number | null
  error_msg: string
}

export function listDatasets() {
  return http.get<Dataset[]>('/datasets/')
}

export function createDataset(data: DatasetInput) {
  return http.post<Dataset>('/datasets/', data)
}

export function updateDataset(id: number, data: Partial<DatasetInput>) {
  return http.patch<Dataset>(`/datasets/${id}/`, data)
}

export function deleteDataset(id: number) {
  return http.delete(`/datasets/${id}/`)
}

export function previewDataset(id: number) {
  return http.post<PreviewResult>(`/datasets/${id}/preview/`)
}

export function runDataset(id: number) {
  return http.post<ExecutionResult>(`/datasets/${id}/run/`)
}
