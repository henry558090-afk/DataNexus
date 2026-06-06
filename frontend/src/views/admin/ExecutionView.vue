<script setup lang="ts">
import { Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { type Execution, downloadExecution, listExecutions } from '@/api/execution'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const rows = ref<Execution[]>([])
const page = ref(1)
const total = ref(0)
const pageSize = 20

const statusMeta: Record<string, { text: string; type: 'success' | 'danger' | 'info' }> = {
  success: { text: '成功', type: 'success' },
  failed: { text: '失败', type: 'danger' },
  running: { text: '运行中', type: 'info' },
}

async function load() {
  loading.value = true
  try {
    const { data } = await listExecutions({ page: page.value })
    rows.value = data.results
    total.value = data.count
  } finally {
    loading.value = false
  }
}

function onPage(p: number) {
  page.value = p
  load()
}

async function handleDownload(row: Execution) {
  if (row.status !== 'success') {
    ElMessage.warning('该执行没有可下载文件')
    return
  }
  await downloadExecution(row.id, `${row.dataset_name}.xlsx`)
}

function fmtTime(s: string): string {
  return s ? s.slice(0, 19).replace('T', ' ') : '-'
}

onMounted(load)
</script>

<template>
  <PageContainer title="执行记录" subtitle="数据集运行历史与生成的文件">
    <template #actions>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="dataset_name" label="数据集" min-width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status]?.type ?? 'info'" size="small">
              {{ statusMeta[row.status]?.text ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="row_count" label="行数" width="100" />
        <el-table-column label="开始时间" min-width="170">
          <template #default="{ row }">{{ fmtTime(row.started_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              text
              type="primary"
              :icon="Download"
              :disabled="row.status !== 'success'"
              @click="handleDownload(row)"
            >
              下载
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有执行记录" />
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
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
