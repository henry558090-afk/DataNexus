<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'

import { type AuditLog, listAuditLogs } from '@/api/audit'
import { type AuditStats, getAuditStats } from '@/api/dataset'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const rows = ref<AuditLog[]>([])
const page = ref(1)
const total = ref(0)
const pageSize = 20
const action = ref('')

const stats = ref<AuditStats | null>(null)
const actionLabel: Record<string, string> = {
  login: '登录',
  run: '运行数据集',
  download: '下载文件',
}

const actionTag: Record<string, 'success' | 'warning' | 'info'> = {
  login: 'info',
  run: 'warning',
  download: 'success',
}

// 每日趋势：归一化到 0-100% 高度
const trend = computed(() => {
  const days = stats.value?.by_day ?? []
  const max = Math.max(1, ...days.map((d) => d.count))
  return days.map((d) => ({ ...d, pct: Math.round((d.count / max) * 100) }))
})
const topUserMax = computed(() => Math.max(1, ...(stats.value?.top_users ?? []).map((u) => u.count)))

function fmtTime(s: string): string {
  return s ? s.slice(0, 19).replace('T', ' ') : '-'
}
function fmtDay(s: string): string {
  return s ? s.slice(5) : '' // MM-DD
}

async function load() {
  loading.value = true
  try {
    const [logs, st] = await Promise.all([
      listAuditLogs({ page: page.value, action: action.value || undefined }),
      page.value === 1 && !action.value ? getAuditStats(30) : Promise.resolve(null),
    ])
    rows.value = logs.data.results
    total.value = logs.data.count
    if (st) stats.value = st.data
  } finally {
    loading.value = false
  }
}

function onFilter() {
  page.value = 1
  load()
}

function onPage(p: number) {
  page.value = p
  load()
}

onMounted(load)
</script>

<template>
  <PageContainer title="审计日志" subtitle="谁、何时、从哪个 IP 做了什么">
    <template #actions>
      <el-select v-model="action" placeholder="全部动作" clearable class="flt" @change="onFilter">
        <el-option label="登录" value="login" />
        <el-option label="运行数据集" value="run" />
        <el-option label="下载文件" value="download" />
      </el-select>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </template>

    <section v-if="stats && stats.total" class="stats">
      <div class="panel">
        <div class="panel-head">
          <span class="pt">动作分布</span>
          <span class="psub">近 30 天 · 共 {{ stats.total }} 条</span>
        </div>
        <div class="bars">
          <div v-for="a in stats.by_action" :key="a.action" class="bar-row">
            <span class="bar-label">{{ actionLabel[a.action] ?? a.action }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: Math.round((a.count / stats.total) * 100) + '%' }"
              />
            </div>
            <span class="bar-val">{{ a.count }}</span>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head">
          <span class="pt">每日趋势</span>
          <span class="psub">近 30 天</span>
        </div>
        <div class="trend">
          <div v-for="(d, i) in trend" :key="d.day" class="col" :title="`${d.day}：${d.count}`">
            <div class="col-bar" :style="{ height: Math.max(d.pct, 3) + '%' }" />
            <span v-if="i % 5 === 0 || i === trend.length - 1" class="col-x">{{
              fmtDay(d.day)
            }}</span>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head">
          <span class="pt">活跃用户 Top</span>
          <span class="psub">近 30 天</span>
        </div>
        <div class="bars">
          <div v-for="u in stats.top_users" :key="u.username" class="bar-row">
            <span class="bar-label">{{ u.username }}</span>
            <div class="bar-track">
              <div class="bar-fill alt" :style="{ width: (u.count / topUserMax) * 100 + '%' }" />
            </div>
            <span class="bar-val">{{ u.count }}</span>
          </div>
          <div v-if="!stats.top_users.length" class="muted small">暂无数据</div>
        </div>
      </div>
    </section>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column label="时间" min-width="170">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="username" label="账号" min-width="120" />
        <el-table-column label="动作" width="120">
          <template #default="{ row }">
            <el-tag :type="actionTag[row.action] ?? 'info'" size="small">
              {{ row.action_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="对象" min-width="160" />
        <el-table-column prop="ip" label="IP" min-width="130" />
        <template #empty>
          <el-empty description="暂无审计记录" />
        </template>
      </el-table>
      <div v-if="total > pageSize" class="pager">
        <el-pagination
          layout="prev, pager, next, total"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="onPage"
        />
      </div>
    </el-card>
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.flt {
  width: 150px;
  margin-right: 8px;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* ---- 审计可视化 ---- */
.stats {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: 16px;
  margin-bottom: 18px;
}
.panel {
  background: var(--surface, #fff);
  border: 1px solid var(--border, #e9edf4);
  border-radius: var(--r-lg, 16px);
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(26, 31, 43, 0.04));
  padding: 16px 18px;
}
.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}
.pt {
  font-weight: 650;
  font-size: 14px;
}
.psub {
  font-size: 12px;
  color: var(--ink-3, #889);
}
.bars {
  display: flex;
  flex-direction: column;
  gap: 11px;
}
.bar-row {
  display: grid;
  grid-template-columns: 84px 1fr 34px;
  align-items: center;
  gap: 10px;
}
.bar-label {
  font-size: 13px;
  color: var(--ink-2, #565f70);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bar-track {
  height: 8px;
  background: var(--surface-2, #f9fafd);
  border-radius: 999px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 999px;
  background: var(--accent, #4b5bd6);
  transition: width var(--dur, 200ms) var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.bar-fill.alt {
  background: #16a34a;
}
.bar-val {
  font-size: 13px;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.trend {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 96px;
}
.col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
  gap: 4px;
}
.col-bar {
  width: 100%;
  max-width: 14px;
  background: var(--accent-weak, #eef0fc);
  border-top: 2px solid var(--accent, #4b5bd6);
  border-radius: 3px 3px 0 0;
  transition: height var(--dur, 200ms) var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.col-x {
  font-size: 9px;
  color: var(--ink-3, #889);
  transform: rotate(-45deg);
  white-space: nowrap;
}
.muted {
  color: var(--ink-3, #889);
}
.small {
  font-size: 12.5px;
}
@media (max-width: 1100px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
@media (prefers-reduced-motion: reduce) {
  .bar-fill,
  .col-bar {
    transition: none;
  }
}
</style>
