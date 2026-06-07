import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  // ---- 管理端（超管 / 辅助管理员）----
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresManager: true },
    children: [
      { path: '', redirect: '/admin/home' },
      {
        path: 'home',
        name: 'admin-home',
        component: () => import('@/views/admin/AdminHome.vue'),
        meta: { title: '工作台' },
      },
      {
        path: 'datasources',
        name: 'admin-datasources',
        component: () => import('@/views/admin/DataSourceView.vue'),
        meta: { title: '数据源' },
      },
      {
        path: 'datasets',
        name: 'admin-datasets',
        component: () => import('@/views/admin/DatasetView.vue'),
        meta: { title: '数据集' },
      },
      {
        path: 'folders',
        name: 'admin-folders',
        component: () => import('@/views/admin/FolderView.vue'),
        meta: { title: '文件夹' },
      },
      {
        path: 'files',
        name: 'admin-files',
        component: () => import('@/views/admin/FileView.vue'),
        meta: { title: '数据文件' },
      },
      {
        path: 'permission',
        name: 'admin-permission',
        component: () => import('@/views/admin/PermissionView.vue'),
        meta: { title: '用户与部门' },
      },
      {
        path: 'audit',
        name: 'admin-audit',
        component: () => import('@/views/admin/AuditView.vue'),
        meta: { title: '审计日志' },
      },
    ],
  },
  // ---- 用户端（普通用户，管理员也可浏览）----
  {
    path: '/',
    component: () => import('@/layouts/UserLayout.vue'),
    children: [
      { path: '', redirect: '/catalog' },
      {
        path: 'catalog',
        name: 'user-catalog',
        component: () => import('@/views/user/CatalogHome.vue'),
        meta: { title: '数据目录' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 守卫：登录校验 + 角色分流
router.beforeEach(async (to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    return { name: 'login' }
  }
  if (to.name === 'login' && token) {
    return { path: '/' }
  }
  if (token) {
    const auth = useAuthStore()
    if (!auth.profile) {
      try {
        await auth.fetchProfile()
      } catch {
        // 401 由 http 拦截器处理
      }
    }
    // 管理端仅管理员可进，否则回用户端
    if (to.meta.requiresManager && !auth.isManager) {
      return { path: '/' }
    }
  }
  return true
})

export default router
