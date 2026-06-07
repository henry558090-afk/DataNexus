<script setup lang="ts">
import { Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { type DataFile, downloadDataFile, listDataFiles } from '@/api/datafile'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const rows = ref<DataFile[]>([])
const page = ref(1)
const total = ref(0)
const pageSize = 20

const statusMeta: Record<string, { text: string; type: 'success' | 'danger' | 'info' }> = {
  success: { text: '成功', type: 'success' },
  failed: { text: '失败', type: 'danger' },
  running: { text: '生成中', type: 'info' },
}

function fmtTime(s: string): string {
  return s ? s.slice(0, 19).replace('T', ' ') : '-'
}
function fmtSize(n: number | null): string {
  if (!n) return '-'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

async function load() {
  loading.value = true
  try {
    const { data } = await listDataFiles({ page: page.value })
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
async function handleDownload(row: DataFile) {
  if (row.status !== 'success') {
    ElMessage.warning('该文件不可下载')
    return
  }
  await downloadDataFile(row.id, row.name)
}

onMounted(load)
</script>

<template>
  <PageContainer title="数据文件" subtitle="所有生成的文件（按文件夹归类，可下载）">
    <template #actions>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="name" label="文件名" min-width="200" />
        <el-table-column prop="folder_name" label="文件夹" min-width="120" />
        <el-table-column prop="dataset_name" label="来源数据集" min-width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status]?.type ?? 'info'" size="small">
              {{ statusMeta[row.status]?.text ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="row_count" label="行数" width="90" />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ fmtSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="生成时间" min-width="160">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              text
              type="primary"
              :icon="Download"
              :disabled="row.status !== 'success'"
              @click="handleDownload(row)"
              >下载</el-button
            >
          </template>
        </el-table-column>
        <template #empty><el-empty description="还没有文件" /></template>
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
