<script setup lang="ts">
import { Coin, Document, Files, TrendCharts } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import http from '@/api/http'

const username = ref('')

const stats = [
  { label: '数据源', value: 0, icon: Coin, color: '#4f6ef7', bg: '#eef1fe' },
  { label: '查询任务', value: 0, icon: Document, color: '#16a34a', bg: '#e7f7ec' },
  { label: '执行记录', value: 0, icon: Files, color: '#d97706', bg: '#fdf0e0' },
  { label: '今日运行', value: 0, icon: TrendCharts, color: '#9333ea', bg: '#f3e9fd' },
]

onMounted(async () => {
  // 拉取当前用户，验证前后端 Token 认证链路打通
  const { data } = await http.get<{ username: string }>('/auth/me/')
  username.value = data.username
})
</script>

<template>
  <div>
    <!-- 欢迎横幅 -->
    <div class="banner">
      <div class="banner-text">
        <h2 class="hello">你好，{{ username || '...' }} 👋</h2>
        <p class="desc">欢迎使用 data-nexus，从这里把 SQL 跑成 Excel、分享给团队。</p>
      </div>
      <div class="banner-art">DN</div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats">
      <el-card v-for="s in stats" :key="s.label" class="stat" shadow="never">
        <div class="stat-inner">
          <div class="stat-icon" :style="{ background: s.bg, color: s.color }">
            <el-icon :size="22"><component :is="s.icon" /></el-icon>
          </div>
          <div>
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 快速开始 -->
    <el-card class="quick" shadow="never">
      <template #header>
        <span class="quick-title">快速开始</span>
      </template>
      <el-steps :active="0" align-center>
        <el-step title="配置数据源" description="接入你的 Oracle（只读）" />
        <el-step title="编写查询任务" description="保存一段 SELECT" />
        <el-step title="运行导出 Excel" description="一键生成明细表" />
        <el-step title="下载 / 分享" description="受控下载中心" />
      </el-steps>
    </el-card>
  </div>
</template>

<style scoped>
.banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(120deg, #4f6ef7 0%, #6b80ff 60%, #8a9bff 100%);
  border-radius: var(--app-radius);
  padding: 28px 32px;
  color: #fff;
  box-shadow: 0 10px 30px rgba(79, 110, 247, 0.28);
  overflow: hidden;
}
.hello {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}
.desc {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}
.banner-art {
  font-size: 56px;
  font-weight: 800;
  opacity: 0.25;
  letter-spacing: 2px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 20px 0;
}
.stat {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.stat-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
}
.stat-label {
  font-size: 13px;
  color: var(--app-text-secondary);
  margin-top: 2px;
}

.quick {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.quick-title {
  font-weight: 600;
}

@media (max-width: 1100px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
