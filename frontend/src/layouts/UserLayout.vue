<script setup lang="ts">
import { Setting, SwitchButton } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const initial = computed(() => (auth.username || '?').charAt(0).toUpperCase())

function handleCommand(command: string): void {
  if (command === 'logout') {
    auth.logout()
    router.push({ name: 'login' })
  } else if (command === 'admin') {
    router.push('/admin')
  }
}
</script>

<template>
  <div class="portal">
    <header class="topbar">
      <div class="brand" @click="router.push('/')">
        <div class="brand-mark">DN</div>
        <span class="brand-name">data-nexus</span>
        <span class="brand-sub">数据门户</span>
      </div>

      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user">
          <el-avatar :size="34" class="avatar">{{ initial }}</el-avatar>
          <span class="user-name">{{ auth.username }}</span>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-if="auth.isManager" command="admin">
              <el-icon><Setting /></el-icon>
              进入管理端
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </header>

    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.portal {
  min-height: 100vh;
  background: radial-gradient(900px 500px at 100% 0%, #eef2ff 0%, transparent 50%), var(--app-bg);
}
.topbar {
  height: 64px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--app-border);
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: linear-gradient(135deg, #4f6ef7, #7c8cff);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.35);
}
.brand-name {
  font-weight: 700;
  font-size: 16px;
}
.brand-sub {
  font-size: 12px;
  color: var(--app-text-secondary);
  padding-left: 8px;
  border-left: 1px solid var(--app-border);
  margin-left: 4px;
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
.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
}
</style>
