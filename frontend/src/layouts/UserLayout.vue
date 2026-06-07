<script setup lang="ts">
import { ArrowDown, Setting, SwitchButton } from '@element-plus/icons-vue'
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
      <div class="bar-inner">
        <div class="brand" @click="router.push('/')">
          <div class="brand-mark">DN</div>
          <span class="brand-name">data-nexus</span>
          <span class="brand-sub">数据门户</span>
        </div>

        <el-dropdown trigger="click" @command="handleCommand">
          <div class="user">
            <div class="avatar">{{ initial }}</div>
            <span class="user-name">{{ auth.username }}</span>
            <el-icon class="chev"><ArrowDown /></el-icon>
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
      </div>
    </header>

    <main class="content">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.portal {
  min-height: 100vh;
  background: var(--bg);
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--border);
}
.bar-inner {
  max-width: 1280px;
  margin: 0 auto;
  height: 60px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.brand-mark {
  width: 32px;
  height: 32px;
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
.brand-name {
  font-weight: 650;
  font-size: 15px;
  letter-spacing: -0.01em;
}
.brand-sub {
  font-size: 12px;
  color: var(--ink-3);
  padding-left: 9px;
  margin-left: 5px;
  border-left: 1px solid var(--border-strong);
}
.user {
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  padding: 5px 10px 5px 6px;
  border-radius: var(--r-full);
  transition: background var(--dur-fast) var(--ease-out);
  outline: none;
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
  color: var(--ink);
}
.chev {
  color: var(--ink-3);
  font-size: 12px;
}
.content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 28px 24px 48px;
}

/* 页面切换：克制的淡入上移 */
.page-enter-active {
  transition:
    opacity var(--dur) var(--ease-out),
    transform var(--dur) var(--ease-out);
}
.page-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
</style>
