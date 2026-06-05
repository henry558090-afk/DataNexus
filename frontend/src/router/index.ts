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
        meta: { title: '工作台' },
      },
      {
        path: 'datasources',
        name: 'datasources',
        component: () => import('@/views/DataSourceView.vue'),
        meta: { title: '数据源' },
      },
      {
        path: 'tasks',
        name: 'tasks',
        component: () => import('@/views/TaskView.vue'),
        meta: { title: '查询任务' },
      },
      {
        path: 'executions',
        name: 'executions',
        component: () => import('@/views/ExecutionView.vue'),
        meta: { title: '执行记录' },
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
