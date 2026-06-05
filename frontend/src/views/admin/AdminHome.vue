<script setup lang="ts">
import { Coin, Document, Files, TrendCharts } from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const stats = [
  { label: '数据源', value: 0, icon: Coin, color: '#4f6ef7', bg: '#eef1fe' },
  { label: '数据集', value: 0, icon: Document, color: '#16a34a', bg: '#e7f7ec' },
  { label: '执行记录', value: 0, icon: Files, color: '#d97706', bg: '#fdf0e0' },
  { label: '今日运行', value: 0, icon: TrendCharts, color: '#9333ea', bg: '#f3e9fd' },
]
</script>

<template>
  <div>
    <div class="banner">
      <div>
        <h2 class="hello">你好，{{ auth.username || '...' }} 👋</h2>
        <p class="desc">在这里配置数据源、编写数据集，把 SQL 跑成 Excel 分享给团队。</p>
      </div>
      <div class="banner-art">DN</div>
    </div>

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

    <el-card class="quick" shadow="never">
      <template #header><span class="quick-title">快速开始</span></template>
      <el-steps :active="0" align-center>
        <el-step title="配置数据源" description="接入 Oracle（只读）" />
        <el-step title="编写数据集" description="保存一段 SELECT" />
        <el-step title="运行导出 Excel" description="一键生成明细表" />
        <el-step title="归类 / 授权" description="放进部门目录" />
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
