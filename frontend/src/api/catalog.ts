import http from '@/api/http'

export interface Folder {
  id: number
  name: string
  parent: number | null
  order: number
  requestable: boolean
  created_at: string
}

export function listFolders() {
  return http.get<Folder[]>('/folders/')
}
export function createFolder(name: string, parent: number | null) {
  return http.post<Folder>('/folders/', { name, parent })
}
export function updateFolder(
  id: number,
  data: Partial<{ name: string; parent: number | null; requestable: boolean }>,
) {
  return http.patch<Folder>(`/folders/${id}/`, data)
}
export function deleteFolder(id: number) {
  return http.delete(`/folders/${id}/`)
}

export interface Department {
  id: number
  name: string
  order: number
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

export interface FolderShare {
  id: number
  folder: number
  subject_department: number | null
  department_name: string | null
  subject_user: number | null
  username: string | null
}
export function listFolderShares(folderId: number) {
  return http.get<FolderShare[]>('/folder-shares/', { params: { folder: folderId } })
}
export function listSharesByUser(userId: number) {
  return http.get<FolderShare[]>('/folder-shares/', { params: { subject_user: userId } })
}
export function listSharesByDept(deptId: number) {
  return http.get<FolderShare[]>('/folder-shares/', { params: { subject_department: deptId } })
}
export function createFolderShare(data: {
  folder: number
  subject_department?: number
  subject_user?: number
}) {
  return http.post<FolderShare>('/folder-shares/', data)
}
export function deleteFolderShare(id: number) {
  return http.delete(`/folder-shares/${id}/`)
}
