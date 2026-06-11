import http from '@/api/http'

export interface DatasetLastRun {
  id: number
  status: string
  row_count: number | null
  created_at: string
}

export interface Dataset {
  id: number
  name: string
  description: string
  datasource: number
  datasource_name: string
  sql_text: string
  target_folder: number | null
  folder_name: string | null
  file_prefix: string
  date_format: string
  cron: string
  interval_minutes: number | null
  keep_count: number | null
  keep_days: number | null
  is_active: boolean
  last_run: DatasetLastRun | null
}

export interface DatasetInput {
  name: string
  description?: string
  datasource: number | null
  sql_text: string
  target_folder?: number | null
  file_prefix?: string
  date_format?: string
  cron?: string
  interval_minutes?: number | null
  keep_count?: number | null
  keep_days?: number | null
}

export interface PreviewResult {
  ok: boolean
  message?: string
  columns?: string[]
  rows?: unknown[][]
}

export interface RunResult {
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
  return http.post<RunResult>(`/datasets/${id}/run/`)
}
// 轮询单个数据文件的运行状态（异步运行后用，S1）
export function getDataFile(id: number) {
  return http.get<RunResult>(`/datafiles/${id}/`)
}
