<script setup lang="ts">
import { ArrowLeft, Download } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { type PortalDetail, downloadPortal, getDatasetDetail } from '@/api/portal'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detail = ref<PortalDetail | null>(null)

const latest = computed(() => detail.value?.executions[0] ?? null)
const history = computed(() => detail.value?.executions.slice(1) ?? [])

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
    detail.value = (await getDatasetDetail(Number(route.params.id))).data
  } finally {
    loading.value = false
  }
}

async function download(execId: number) {
  await downloadPortal(execId, `${detail.value?.name ?? 'data'}.xlsx`)
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <el-button text :icon="ArrowLeft" class="back" @click="router.push('/')"
      >返回数据目录</el-button
    >

    <template v-if="detail">
      <h1 class="title">{{ detail.name }}</h1>
      <p class="desc">{{ detail.description || '暂无说明' }}</p>

      <el-card v-if="latest" class="latest" shadow="never">
        <div class="latest-inner">
          <div>
            <div class="latest-label">最新版本</div>
            <div class="latest-meta">
              {{ latest.row_count }} 行 · {{ fmtSize(latest.file_size) }} ·
              {{ fmtTime(latest.started_at) }}
            </div>
          </div>
          <el-button type="primary" :icon="Download" @click="download(latest.id)">
            下载 Excel
          </el-button>
        </div>
      </el-card>
      <el-empty v-else description="该数据还没有生成文件" />

      <template v-if="history.length">
        <h3 class="hist-title">历史版本</h3>
        <el-card class="card" shadow="never">
          <div v-for="ex in history" :key="ex.id" class="hist-row">
            <span>{{ fmtTime(ex.started_at) }} · {{ ex.row_count }} 行</span>
            <el-button text type="primary" :icon="Download" @click="download(ex.id)"
              >下载</el-button
            >
          </div>
        </el-card>
      </template>
    </template>
  </div>
</template>

<style scoped>
.back {
  margin-bottom: 8px;
}
.title {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 800;
}
.desc {
  margin: 0 0 20px;
  color: var(--app-text-secondary);
}
.latest {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.latest-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.latest-label {
  font-size: 13px;
  color: var(--app-text-secondary);
}
.latest-meta {
  font-size: 16px;
  font-weight: 600;
  margin-top: 4px;
}
.hist-title {
  margin: 24px 0 12px;
  font-size: 16px;
  font-weight: 700;
}
.card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.hist-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 4px;
  border-bottom: 1px solid var(--app-border);
}
.hist-row:last-child {
  border-bottom: none;
}
</style>
