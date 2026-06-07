<script setup lang="ts">
import { Coin, Document, Files, Right, TrendCharts } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { type DataFile, listDataFiles } from '@/api/datafile'
import { type Stats, getStats } from '@/api/stats'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const stats = ref<Stats>({ datasources: 0, datasets: 0, files: 0, today_runs: 0 })
const recent = ref<DataFile[]>([])
const loading = ref(true)

const cards = computed(() => [
  {
    label: '数据源',
    value: stats.value.datasources,
    icon: Coin,
    tone: 'indigo',
    to: '/admin/datasources',
  },
  {
    label: '数据集',
    value: stats.value.datasets,
    icon: Document,
    tone: 'green',
    to: '/admin/datasets',
  },
  { label: '数据文件', value: stats.value.files, icon: Files, tone: 'amber', to: '/admin/files' },
  {
    label: '今日生成',
    value: stats.value.today_runs,
    icon: TrendCharts,
    tone: 'violet',
    to: '/admin/files',
  },
])

const statusMeta: Record<string, { text: string; type: 'success' | 'danger' | 'info' }> = {
  success: { text: '成功', type: 'success' },
  failed: { text: '失败', type: 'danger' },
  running: { text: '生成中', type: 'info' },
}
function fmtTime(s: string): string {
  return s ? s.slice(0, 16).replace('T', ' ') : '-'
}

onMounted(async () => {
  try {
    const [s, f] = await Promise.all([getStats(), listDataFiles()])
    stats.value = s.data
    recent.value = f.data.results.slice(0, 7)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="home">
    <header class="welcome">
      <h1>你好，{{ auth.username || '...' }}</h1>
      <p>配数据源 · 写数据集 · 跑成 Excel 放进文件夹 · 按部门或个人授权。</p>
    </header>

    <div class="stats">
      <button
        v-for="c in cards"
        :key="c.label"
        class="stat"
        :class="c.tone"
        @click="router.push(c.to)"
      >
        <div class="stat-ic">
          <el-icon :size="20"><component :is="c.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </div>
        <el-icon class="stat-go"><Right /></el-icon>
      </button>
    </div>

    <section class="recent">
      <div class="recent-head">
        <span class="rt">最近生成的文件</span>
        <el-button text type="primary" @click="router.push('/admin/files')">查看全部</el-button>
      </div>
      <div class="recent-body">
        <div v-if="loading" class="rlist">
          <div v-for="i in 5" :key="i" class="rrow sk">
            <div class="skeleton sk-ic" />
            <div class="skeleton sk-l1" />
          </div>
        </div>
        <div v-else-if="recent.length" class="rlist">
          <div
            v-for="(f, i) in recent"
            :key="f.id"
            class="rrow rise-in"
            :style="{ animationDelay: i * 30 + 'ms' }"
          >
            <div class="rrow-ic">XLS</div>
            <div class="rrow-main">
              <div class="rrow-name">{{ f.name }}</div>
              <div class="rrow-meta">
                {{ f.folder_name || '未归类' }} · {{ fmtTime(f.created_at) }}
              </div>
            </div>
            <el-tag :type="statusMeta[f.status]?.type ?? 'info'" size="small" effect="light">
              {{ statusMeta[f.status]?.text ?? f.status }}
            </el-tag>
          </div>
        </div>
        <div v-else class="rempty">
          <el-icon :size="26"><Files /></el-icon>
          <p>还没有文件</p>
          <span>去数据集页跑一个，文件会出现在这里</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.welcome h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.welcome p {
  margin: 6px 0 0;
  color: var(--ink-2);
  font-size: 14px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  text-align: left;
  transition:
    transform var(--dur-fast) var(--ease-out),
    box-shadow var(--dur) var(--ease-out),
    border-color var(--dur) var(--ease-out);
}
.stat:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
  border-color: var(--border-strong);
}
.stat-ic {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat.indigo .stat-ic {
  background: #eef0fc;
  color: #4b5bd6;
}
.stat.green .stat-ic {
  background: #e7f7ec;
  color: #16a34a;
}
.stat.amber .stat-ic {
  background: #fdf0e0;
  color: #d97706;
}
.stat.violet .stat-ic {
  background: #f3e9fd;
  color: #9333ea;
}
.stat-body {
  flex: 1;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
}
.stat-label {
  font-size: 13px;
  color: var(--ink-2);
  margin-top: 2px;
}
.stat-go {
  color: var(--ink-3);
  opacity: 0;
  transform: translateX(-4px);
  transition: all var(--dur-fast) var(--ease-out);
}
.stat:hover .stat-go {
  opacity: 1;
  transform: translateX(0);
}
.recent {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.recent-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
}
.rt {
  font-weight: 650;
  font-size: 15px;
}
.recent-body {
  padding: 8px;
}
.rlist {
  display: flex;
  flex-direction: column;
}
.rrow {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 12px;
  border-radius: var(--r);
  transition: background var(--dur-fast) var(--ease-out);
}
.rrow:hover {
  background: var(--surface-2);
}
.rrow-ic {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: color-mix(in srgb, var(--success) 12%, white);
  color: var(--success);
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.rrow-main {
  flex: 1;
  min-width: 0;
}
.rrow-name {
  font-size: 14px;
  font-weight: 550;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rrow-meta {
  font-size: 12.5px;
  color: var(--ink-3);
  margin-top: 2px;
}
.rrow.sk .sk-ic {
  width: 34px;
  height: 34px;
  border-radius: 9px;
}
.rrow.sk .sk-l1 {
  height: 13px;
  width: 40%;
}
.rempty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px;
  color: var(--ink-3);
}
.rempty p {
  margin: 12px 0 2px;
  color: var(--ink-2);
  font-size: 14px;
}
.rempty span {
  font-size: 12px;
}
@media (max-width: 1100px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
