<script setup lang="ts">
import { Check, Close, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import {
  type AccessRequest,
  approveAccessRequest,
  listAccessRequests,
  rejectAccessRequest,
} from '@/api/dataset'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const rows = ref<AccessRequest[]>([])
const status = ref<'pending' | 'approved' | 'rejected'>('pending')
const actingId = ref<number | null>(null)

const statusMeta: Record<string, { text: string; type: 'warning' | 'success' | 'info' }> = {
  pending: { text: '待审批', type: 'warning' },
  approved: { text: '已通过', type: 'success' },
  rejected: { text: '已拒绝', type: 'info' },
}

function fmtTime(s: string): string {
  return s ? s.slice(0, 16).replace('T', ' ') : '-'
}

async function load() {
  loading.value = true
  try {
    const { data } = await listAccessRequests(status.value)
    rows.value = data
  } finally {
    loading.value = false
  }
}

async function handleApprove(row: AccessRequest) {
  actingId.value = row.id
  try {
    await approveAccessRequest(row.id)
    ElMessage.success(`已通过：${row.username} 现在可访问「${row.folder_name}」`)
    await load()
  } finally {
    actingId.value = null
  }
}

async function handleReject(row: AccessRequest) {
  actingId.value = row.id
  try {
    await rejectAccessRequest(row.id)
    ElMessage.success('已拒绝该申请')
    await load()
  } finally {
    actingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <PageContainer title="审批中心" subtitle="用户申请访问某文件夹，通过后自动授权给该用户">
    <template #actions>
      <el-radio-group v-model="status" @change="load">
        <el-radio-button value="pending">待审批</el-radio-button>
        <el-radio-button value="approved">已通过</el-radio-button>
        <el-radio-button value="rejected">已拒绝</el-radio-button>
      </el-radio-group>
      <el-button :icon="Refresh" class="ml" @click="load">刷新</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="username" label="申请人" min-width="120" />
        <el-table-column label="申请文件夹" min-width="150">
          <template #default="{ row }">
            <span class="folder">{{ row.folder_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="理由" min-width="200">
          <template #default="{ row }">
            <span :class="{ muted: !row.reason }">{{ row.reason || '（未填写）' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status]?.type ?? 'info'" size="small">
              {{ statusMeta[row.status]?.text ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="150">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button
                text
                type="success"
                :icon="Check"
                :loading="actingId === row.id"
                @click="handleApprove(row)"
                >通过</el-button
              >
              <el-button
                text
                type="danger"
                :icon="Close"
                :loading="actingId === row.id"
                @click="handleReject(row)"
                >拒绝</el-button
              >
            </template>
            <span v-else class="muted">已处理</span>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty
            :description="
              status === 'pending' ? '没有待审批的申请，一切都处理完了' : '没有相关记录'
            "
          />
        </template>
      </el-table>
    </el-card>
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--app-border, #e9edf4);
  border-radius: var(--app-radius, 12px);
}
.ml {
  margin-left: 8px;
}
.folder {
  font-weight: 550;
}
.muted {
  color: var(--ink-3, #889);
}
</style>
