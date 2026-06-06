import http from '@/api/http'

export interface Category {
  id: number
  name: string
  department: number
  department_name: string
  order: number
}

export interface Department {
  id: number
  name: string
  order: number
  categories: Category[]
}

export function listDepartments() {
  return http.get<Department[]>('/departments/')
}

export function createDepartment(name: string) {
  return http.post<Department>('/departments/', { name })
}

export function deleteDepartment(id: number) {
  return http.delete(`/departments/${id}/`)
}

export function listCategories() {
  return http.get<Category[]>('/categories/')
}

export function createCategory(name: string, department: number) {
  return http.post<Category>('/categories/', { name, department })
}

export function deleteCategory(id: number) {
  return http.delete(`/categories/${id}/`)
}
