import http from '@/api/http'

export interface DataSource {
  id: number
  name: string
  host: string
  port: number
  service_name: string
  username: string
  has_password: boolean
  created_at: string
}

export interface DataSourceInput {
  name: string
  host: string
  port: number
  service_name: string
  username: string
  password?: string
}

export interface TestResult {
  ok: boolean
  message: string
}

export function listDataSources() {
  return http.get<DataSource[]>('/datasources/')
}

export function createDataSource(data: DataSourceInput) {
  return http.post<DataSource>('/datasources/', data)
}

export function updateDataSource(id: number, data: Partial<DataSourceInput>) {
  return http.patch<DataSource>(`/datasources/${id}/`, data)
}

export function deleteDataSource(id: number) {
  return http.delete(`/datasources/${id}/`)
}

// 测试已保存数据源
export function testDataSource(id: number) {
  return http.post<TestResult>(`/datasources/${id}/test/`)
}

// 用表单参数预检（保存前）
export function testDataSourceParams(data: DataSourceInput) {
  return http.post<TestResult>('/datasources/test-connection/', data)
}
