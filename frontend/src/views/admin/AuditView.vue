<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import { type AuditLog, listAuditLogs } from '@/api/audit'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const rows = ref<AuditLog[]>([])
const page = ref(1)
const total = ref(0)
const pageSize = 20
const action = ref('')

const actionTag: Record<string, 'success' | 'warning' | 'info'> = {
  login: 'info',
  run: 'warning',
  download: 'success',
}

function fmtTime(s: string): string {
  return s ? s.slice(0, 19).replace('T', ' ') : '-'
}

async function load() {
  loading.value = true
  try {
    const { data } = await listAuditLogs({ page: page.value, action: action.value || undefined })
    rows.value = data.results
    total.value = data.count
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
</style>
