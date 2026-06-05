<script setup lang="ts">
import { Coin, DataLine, Document, Files, SwitchButton } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const pageTitle = computed(() => (route.meta.title as string) ?? '')
const initial = computed(() => (auth.username || '?').charAt(0).toUpperCase())

const menus = [
  { index: '/dashboard', title: '工作台', icon: DataLine },
  { index: '/datasources', title: '数据源', icon: Coin },
  { index: '/tasks', title: '查询任务', icon: Document },
  { index: '/executions', title: '执行记录', icon: Files },
]

function handleLogout(): void {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="232px" class="aside">
      <div class="brand">
        <div class="brand-mark">DN</div>
        <div class="brand-text">
          <span class="brand-name">data-nexus</span>
          <span class="brand-sub">数据共享平台</span>
        </div>
      </div>

      <el-menu router :default-active="route.path" class="menu">
        <el-menu-item v-for="m in menus" :key="m.index" :index="m.index">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="page-title">{{ pageTitle }}</span>

        <el-dropdown trigger="click" @command="handleLogout">
          <div class="user">
            <el-avatar :size="32" class="avatar">{{ initial }}</el-avatar>
            <span class="user-name">{{ auth.username }}</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}

/* ---- 侧边栏（浅色） ---- */
.aside {
  background: var(--app-surface);
  border-right: 1px solid var(--app-border);
  display: flex;
  flex-direction: column;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 64px;
  padding: 0 20px;
}
.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f6ef7, #7c8cff);
  color: #fff;
  font-weight: 700;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.35);
}
.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}
.brand-name {
  font-weight: 700;
  font-size: 15px;
}
.brand-sub {
  font-size: 12px;
  color: var(--app-text-secondary);
}

.menu {
  border-right: none;
  padding: 10px 12px;
  flex: 1;
}
.menu :deep(.el-menu-item) {
  height: 44px;
  border-radius: 10px;
  margin-bottom: 4px;
  color: #5a6478;
  font-weight: 500;
}
.menu :deep(.el-menu-item:hover) {
  background: #f3f5fb;
  color: var(--app-text);
}
.menu :deep(.el-menu-item.is-active) {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}

/* ---- 顶栏 ---- */
.header {
  height: 64px;
  background: var(--app-surface);
  border-bottom: 1px solid var(--app-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.page-title {
  font-size: 17px;
  font-weight: 600;
}
.user {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 10px;
  transition: background 0.2s;
}
.user:hover {
  background: #f3f5fb;
}
.avatar {
  background: linear-gradient(135deg, #4f6ef7, #7c8cff);
  font-weight: 600;
}
.user-name {
  font-size: 14px;
  font-weight: 500;
}

/* ---- 主体 ---- */
.main {
  background: var(--app-bg);
  padding: 24px;
}
</style>
