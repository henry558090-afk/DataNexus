import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/DashboardView.vue'),
      },
      {
        path: 'datasources',
        name: 'datasources',
        component: () => import('@/views/DataSourceView.vue'),
      },
      {
        path: 'tasks',
        name: 'tasks',
        component: () => import('@/views/TaskView.vue'),
      },
      {
        path: 'executions',
        name: 'executions',
        component: () => import('@/views/ExecutionView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫：未登录跳登录页；已登录访问登录页回首页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    return { name: 'login' }
  }
  if (to.name === 'login' && token) {
    return { path: '/' }
  }
  return true
})

export default router
