<script setup lang="ts">
import { Coin, Document, Files, TrendCharts } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { type DataFile, listDataFiles } from '@/api/datafile'
import { type Stats, getStats } from '@/api/stats'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const stats = ref<Stats>({ datasources: 0, datasets: 0, files: 0, today_runs: 0 })
const recent = ref<DataFile[]>([])

const cards = computed(() => [
  {
    label: '数据源',
    value: stats.value.datasources,
    icon: Coin,
    color: '#4f6ef7',
    bg: '#eef1fe',
    to: '/admin/datasources',
  },
  {
    label: '数据集',
    value: stats.value.datasets,
    icon: Document,
    color: '#16a34a',
    bg: '#e7f7ec',
    to: '/admin/datasets',
  },
  {
    label: '数据文件',
    value: stats.value.files,
    icon: Files,
    color: '#d97706',
    bg: '#fdf0e0',
    to: '/admin/files',
  },
  {
    label: '今日生成',
    value: stats.value.today_runs,
    icon: TrendCharts,
    color: '#9333ea',
    bg: '#f3e9fd',
    to: '/admin/files',
  },
])

const statusMeta: Record<string, { text: string; type: 'success' | 'danger' | 'info' }> = {
  success: { text: '成功', type: 'success' },
  failed: { text: '失败', type: 'danger' },
  running: { text: '生成中', type: 'info' },
}
function fmtTime(s: string): string {
  return s ? s.slice(0, 19).replace('T', ' ') : '-'
}

onMounted(async () => {
  const [s, f] = await Promise.all([getStats(), listDataFiles()])
  stats.value = s.data
  recent.value = f.data.results.slice(0, 8)
})
</script>

<template>
  <div>
    <div class="banner">
      <div>
        <h2 class="hello">你好，{{ auth.username || '...' }} 👋</h2>
        <p class="desc">配数据源、写数据集，把 SQL 跑成 Excel 放进文件夹，按部门分享。</p>
      </div>
      <div class="banner-art">DN</div>
    </div>

    <div class="stats">
      <el-card
        v-for="c in cards"
        :key="c.label"
        class="stat"
        shadow="never"
        @click="router.push(c.to)"
      >
        <div class="stat-inner">
          <div class="stat-icon" :style="{ background: c.bg, color: c.color }">
            <el-icon :size="22"><component :is="c.icon" /></el-icon>
          </div>
          <div>
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <el-card class="recent" shadow="never">
      <template #header>
        <div class="rhead">
          <span class="rtitle">最近生成的文件</span>
          <el-button text type="primary" @click="router.push('/admin/files')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recent">
        <el-table-column prop="name" label="文件名" min-width="200" />
        <el-table-column prop="folder_name" label="文件夹" min-width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status]?.type ?? 'info'" size="small">
              {{ statusMeta[row.status]?.text ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有文件，去数据集页跑一个吧" :image-size="60" />
        </template>
      </el-table>
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
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.stat:hover {
  box-shadow: var(--app-shadow);
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
.recent {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.rhead {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rtitle {
  font-weight: 600;
}
@media (max-width: 1100px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
