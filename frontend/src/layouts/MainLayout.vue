<script setup lang="ts">
import { DataLine, Coin, List, Document, SwitchButton } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function handleLogout(): void {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="210px" class="aside">
      <div class="logo">data-nexus</div>
      <el-menu router :default-active="$route.path" class="menu">
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/datasources">
          <el-icon><Coin /></el-icon>
          <span>数据源</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><List /></el-icon>
          <span>查询任务</span>
        </el-menu-item>
        <el-menu-item index="/executions">
          <el-icon><Document /></el-icon>
          <span>执行记录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="title">数据共享平台</span>
        <div class="user">
          <span>{{ auth.username }}</span>
          <el-button link type="primary" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: #001529;
}
.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-weight: 600;
  font-size: 18px;
}
.menu {
  border-right: none;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
}
.title {
  font-weight: 600;
}
.user {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
