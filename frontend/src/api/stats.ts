import http from '@/api/http'

export interface Stats {
  datasources: number
  datasets: number
  files: number
  today_runs: number
}

export function getStats() {
  return http.get<Stats>('/stats/')
}
