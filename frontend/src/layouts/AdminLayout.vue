<script setup lang="ts">
import {
  Coin,
  DataLine,
  Document,
  Files,
  Folder,
  Lock,
  List,
  OfficeBuilding,
  Stamp,
  SwitchButton,
  User as UserIcon,
} from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const pageTitle = computed(() => (route.meta.title as string) ?? '')
const initial = computed(() => (auth.username || '?').charAt(0).toUpperCase())

const groups = [
  { label: '', items: [{ index: '/admin/home', title: '工作台', icon: DataLine }] },
  {
    label: '数据',
    items: [
      { index: '/admin/datasources', title: '数据源', icon: Coin },
      { index: '/admin/datasets', title: '数据集', icon: Document },
      { index: '/admin/folders', title: '目录管理', icon: Folder },
      { index: '/admin/files', title: '数据文件', icon: Files },
    ],
  },
  {
    label: '权限',
    items: [
      { index: '/admin/permission', title: '权限管理', icon: Lock },
      { index: '/admin/approvals', title: '审批中心', icon: Stamp },
      { index: '/admin/departments', title: '部门管理', icon: OfficeBuilding },
      { index: '/admin/users', title: '人员管理', icon: UserIcon },
    ],
  },
  { label: '系统', items: [{ index: '/admin/audit', title: '审计日志', icon: List }] },
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
          <span class="brand-sub">管理端</span>
        </div>
      </div>

      <el-menu router :default-active="route.path" class="menu">
        <template v-for="g in groups" :key="g.label">
          <div v-if="g.label" class="group-label">{{ g.label }}</div>
          <el-menu-item v-for="m in g.items" :key="m.index" :index="m.index">
            <el-icon><component :is="m.icon" /></el-icon>
            <span>{{ m.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="right">
          <el-button text @click="router.push('/')">切换到用户端</el-button>
          <el-dropdown trigger="click" @command="handleLogout">
            <div class="user">
              <div class="avatar">{{ initial }}</div>
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
        </div>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}
.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  height: 60px;
  padding: 0 18px;
  border-bottom: 1px solid var(--border);
}
.brand-mark {
  width: 34px;
  height: 34px;
  border-radius: var(--r-sm);
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: -0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}
.brand-name {
  font-weight: 650;
  font-size: 15px;
  letter-spacing: -0.01em;
}
.brand-sub {
  font-size: 12px;
  color: var(--ink-3);
}
.menu {
  border-right: none;
  padding: 12px 12px;
  flex: 1;
  overflow: auto;
}
.group-label {
  font-size: 11px;
  font-weight: 650;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ink-3);
  padding: 14px 12px 6px;
}
.menu :deep(.el-menu-item) {
  height: 42px;
  border-radius: var(--r-sm);
  margin-bottom: 2px;
  color: var(--ink-2);
  font-weight: 500;
  transition: all var(--dur-fast) var(--ease-out);
}
.menu :deep(.el-menu-item:hover) {
  background: var(--surface-2);
  color: var(--ink);
}
.menu :deep(.el-menu-item.is-active) {
  background: var(--accent-weak);
  color: var(--accent);
  font-weight: 600;
}
.header {
  height: 60px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
}
.page-title {
  font-size: 17px;
  font-weight: 650;
  letter-spacing: -0.01em;
}
.right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user {
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  padding: 5px 10px 5px 6px;
  border-radius: var(--r-full);
  transition: background var(--dur-fast) var(--ease-out);
}
.user:hover {
  background: var(--surface-2);
}
.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-name {
  font-size: 14px;
  font-weight: 550;
}
.main {
  background: var(--bg);
  padding: 24px;
}
.fade-enter-active {
  transition:
    opacity var(--dur) var(--ease-out),
    transform var(--dur) var(--ease-out);
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
</style>
