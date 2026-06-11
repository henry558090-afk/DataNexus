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
export function runDataset(id: number, params?: Record<string, unknown>) {
  return http.post<RunResult>(`/datasets/${id}/run/`, params ? { params } : undefined)
}
// v0.26 图表数据：对最新成功文件按 x 分组聚合 y
export function getChartData(id: number, x: string, y?: string, agg: 'sum' | 'count' | 'avg' = 'sum') {
  return http.get<{ labels: string[]; values: number[]; agg: string }>(
    `/datasets/${id}/chart-data/`,
    { params: { x, y, agg } },
  )
}
// 轮询单个数据文件的运行状态（异步运行后用，S1）
export function getDataFile(id: number) {
  return http.get<RunResult>(`/datafiles/${id}/`)
}

// ---- v0.23 管理员效率 ----
export interface RunHealth {
  days: number
  total: number
  success: number
  failed: number
  running: number
  success_rate: number | null
  avg_duration_ms: number | null
  recent_failures: { id: number; dataset: string | null; name: string; error_msg: string; created_at: string }[]
  slowest_datasets: { dataset: number; dataset__name: string; avg_ms: number; runs: number }[]
}
export function batchRunDatasets(ids: number[]) {
  return http.post<{ count: number }>('/datasets/batch-run/', { ids })
}
export function batchRetention(ids: number[], keep_count?: number | null, keep_days?: number | null) {
  return http.post<{ updated: number }>('/datasets/batch-retention/', { ids, keep_count, keep_days })
}
export function getRunHealth(days = 7) {
  return http.get<RunHealth>(`/datasets/run-health/?days=${days}`)
}

// ---- v0.25 订阅推送 ----
export interface Subscription {
  id: number
  dataset: number
  dataset_name: string
  channel: 'email' | 'webhook'
  target: string
  is_active: boolean
  created_at: string
}
export function listSubscriptions(dataset?: number) {
  return http.get<Subscription[]>('/subscriptions/', { params: { dataset } })
}
export function createSubscription(data: {
  dataset: number
  channel: string
  target: string
}) {
  return http.post<Subscription>('/subscriptions/', data)
}
export function deleteSubscription(id: number) {
  return http.delete(`/subscriptions/${id}/`)
}

// ---- v0.25 访问申请审批（管理员）----
export interface AccessRequest {
  id: number
  username: string
  folder: number
  folder_name: string
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}
export function listAccessRequests(status = 'pending') {
  return http.get<AccessRequest[]>('/access-requests/', { params: { status } })
}
export function approveAccessRequest(id: number) {
  return http.post(`/access-requests/${id}/approve/`)
}
export function rejectAccessRequest(id: number) {
  return http.post(`/access-requests/${id}/reject/`)
}
