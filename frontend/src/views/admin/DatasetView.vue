<script setup lang="ts">
import { Delete, Download, Edit, Plus, View, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import {
  type Dataset,
  type DatasetInput,
  type PreviewResult,
  createDataset,
  deleteDataset,
  listDatasets,
  previewDataset,
  runDataset,
  updateDataset,
} from '@/api/dataset'
import { type Category, listCategories } from '@/api/catalog'
import { type DataSource, listDataSources } from '@/api/datasource'
import { downloadExecution } from '@/api/execution'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const rows = ref<Dataset[]>([])
const datasources = ref<DataSource[]>([])
const categories = ref<Category[]>([])

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const previewVisible = ref(false)
const previewLoading = ref(false)
const preview = ref<PreviewResult | null>(null)

const runningId = ref<number | null>(null)

const form = reactive<DatasetInput>({
  name: '',
  description: '',
  datasource: null,
  category: null,
  sql_text: '',
})

type ScheduleType = 'manual' | 'interval' | 'daily' | 'cron'
const schedule = reactive({ type: 'manual' as ScheduleType, interval: 60, time: '08:00', cron: '' })

function resetSchedule() {
  schedule.type = 'manual'
  schedule.interval = 60
  schedule.time = '08:00'
  schedule.cron = ''
}

function scheduleToFields(): { cron: string; interval_minutes: number | null } {
  if (schedule.type === 'interval') return { cron: '', interval_minutes: schedule.interval }
  if (schedule.type === 'daily') {
    const [h, m] = schedule.time.split(':')
    return { cron: `${Number(m)} ${Number(h)} * * *`, interval_minutes: null }
  }
  if (schedule.type === 'cron') return { cron: schedule.cron.trim(), interval_minutes: null }
  return { cron: '', interval_minutes: null }
}

function fieldsToSchedule(row: Dataset) {
  resetSchedule()
  if (row.cron) {
    const p = row.cron.trim().split(/\s+/)
    if (
      p.length === 5 &&
      p[2] === '*' &&
      p[3] === '*' &&
      p[4] === '*' &&
      /^\d+$/.test(p[0]) &&
      /^\d+$/.test(p[1])
    ) {
      schedule.type = 'daily'
      schedule.time = `${p[1].padStart(2, '0')}:${p[0].padStart(2, '0')}`
    } else {
      schedule.type = 'cron'
      schedule.cron = row.cron
    }
  } else if (row.interval_minutes) {
    schedule.type = 'interval'
    schedule.interval = row.interval_minutes
  }
}

function scheduleSummary(row: Dataset): string {
  if (row.cron) {
    const p = row.cron.trim().split(/\s+/)
    if (p.length === 5 && p[2] === '*' && p[3] === '*' && p[4] === '*') {
      return `每天 ${p[1].padStart(2, '0')}:${p[0].padStart(2, '0')}`
    }
    return `cron: ${row.cron}`
  }
  if (row.interval_minutes) return `每 ${row.interval_minutes} 分钟`
  return '手动'
}

async function load() {
  loading.value = true
  try {
    rows.value = (await listDatasets()).data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    description: '',
    datasource: null,
    category: null,
    sql_text: '',
  })
  resetSchedule()
  dialogVisible.value = true
}

function openEdit(row: Dataset) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    description: row.description,
    datasource: row.datasource,
    category: row.category,
    sql_text: row.sql_text,
  })
  fieldsToSchedule(row)
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name || !form.datasource || !form.sql_text) {
    ElMessage.warning('请填写名称、数据源、SQL')
    return
  }
  saving.value = true
  try {
    const payload = { ...form, ...scheduleToFields() }
    if (editingId.value) {
      await updateDataset(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await createDataset(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handlePreview(row: Dataset) {
  previewVisible.value = true
  previewLoading.value = true
  preview.value = null
  try {
    const { data } = await previewDataset(row.id)
    preview.value = data
    if (!data.ok) ElMessage.error(data.message || '预览失败')
  } finally {
    previewLoading.value = false
  }
}

async function handleRun(row: Dataset) {
  runningId.value = row.id
  try {
    const { data } = await runDataset(row.id)
    if (data.status === 'success') {
      ElMessage.success(`运行成功，共 ${data.row_count} 行`)
    } else {
      ElMessage.error(`运行失败：${data.error_msg}`)
    }
    await load()
  } finally {
    runningId.value = null
  }
}

async function handleDownload(row: Dataset) {
  if (!row.latest || row.latest.status !== 'success') {
    ElMessage.warning('暂无可下载的文件，请先运行')
    return
  }
  await downloadExecution(row.latest.id, `${row.name}.xlsx`)
}

async function handleDelete(row: Dataset) {
  await ElMessageBox.confirm(`确认删除数据集「${row.name}」？`, '提示', { type: 'warning' })
  await deleteDataset(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await Promise.all([load(), loadDatasources(), loadCategories()])
})

async function loadDatasources() {
  datasources.value = (await listDataSources()).data
}

async function loadCategories() {
  categories.value = (await listCategories()).data
}
</script>

<template>
  <PageContainer title="数据集" subtitle="编写 SQL，运行并导出 Excel">
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建数据集</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="datasource_name" label="数据源" min-width="120" />
        <el-table-column label="定时" min-width="120">
          <template #default="{ row }">{{ scheduleSummary(row) }}</template>
        </el-table-column>
        <el-table-column label="最新结果" min-width="150">
          <template #default="{ row }">
            <template v-if="row.latest">
              <el-tag v-if="row.latest.status === 'success'" type="success" size="small">
                {{ row.latest.row_count }} 行
              </el-tag>
              <el-tag v-else-if="row.latest.status === 'failed'" type="danger" size="small">
                失败
              </el-tag>
              <el-tag v-else type="info" size="small">运行中</el-tag>
            </template>
            <span v-else class="muted">未运行</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="330" fixed="right">
          <template #default="{ row }">
            <el-button
              text
              type="primary"
              :icon="VideoPlay"
              :loading="runningId === row.id"
              @click="handleRun(row)"
            >
              运行
            </el-button>
            <el-button text :icon="View" @click="handlePreview(row)">预览</el-button>
            <el-button text :icon="Download" @click="handleDownload(row)">下载</el-button>
            <el-button text :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button text type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有数据集，点击右上角新建" />
        </template>
      </el-table>
    </el-card>

    <!-- 新建 / 编辑 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑数据集' : '新建数据集'"
      width="640px"
    >
      <el-form label-width="72px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如：应收账款明细表" />
        </el-form-item>
        <el-form-item label="数据源" required>
          <el-select v-model="form.datasource" placeholder="选择数据源" style="width: 100%">
            <el-option
              v-for="d in datasources"
              :key="d.id"
              :label="`${d.name}（${d.db_type === 'mysql' ? 'MySQL' : 'Oracle'}）`"
              :value="d.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="归类">
          <el-select
            v-model="form.category"
            placeholder="未归类（用户端不可见，仅管理员）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="c in categories"
              :key="c.id"
              :label="`${c.department_name} / ${c.name}`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" placeholder="可选" />
        </el-form-item>
        <el-form-item label="SQL" required>
          <el-input
            v-model="form.sql_text"
            type="textarea"
            :rows="8"
            placeholder="仅支持只读 SELECT 查询"
            spellcheck="false"
          />
        </el-form-item>
        <el-form-item label="定时">
          <el-radio-group v-model="schedule.type">
            <el-radio-button value="manual">手动</el-radio-button>
            <el-radio-button value="interval">间隔</el-radio-button>
            <el-radio-button value="daily">每天</el-radio-button>
            <el-radio-button value="cron">Cron</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="schedule.type === 'interval'" label=" ">
          每
          <el-input-number v-model="schedule.interval" :min="1" :max="10080" class="mx" />
          分钟运行一次
        </el-form-item>
        <el-form-item v-else-if="schedule.type === 'daily'" label=" ">
          每天
          <el-time-picker v-model="schedule.time" format="HH:mm" value-format="HH:mm" class="mx" />
          运行
        </el-form-item>
        <el-form-item v-else-if="schedule.type === 'cron'" label=" ">
          <el-input v-model="schedule.cron" placeholder="分 时 日 月 周，如 0 8 * * *" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 数据预览 -->
    <el-dialog v-model="previewVisible" title="数据预览（前 50 行）" width="80%">
      <div v-loading="previewLoading">
        <el-table v-if="preview?.ok" :data="preview.rows" border height="420" size="small">
          <el-table-column
            v-for="(col, i) in preview.columns"
            :key="i"
            :label="col"
            :prop="String(i)"
            min-width="120"
          >
            <template #default="{ row }">{{ row[i] }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else-if="!previewLoading" :description="preview?.message || '无数据'" />
      </div>
    </el-dialog>
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.muted {
  color: var(--app-text-secondary);
}
.mx {
  margin: 0 8px;
}
</style>
