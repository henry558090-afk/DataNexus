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
import { type Folder, listFolders } from '@/api/catalog'
import { type DataSource, listDataSources } from '@/api/datasource'
import { downloadDataFile } from '@/api/datafile'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const rows = ref<Dataset[]>([])
const datasources = ref<DataSource[]>([])
const folders = ref<Folder[]>([])

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const runningId = ref<number | null>(null)

const previewVisible = ref(false)
const previewLoading = ref(false)
const preview = ref<PreviewResult | null>(null)

const form = reactive<DatasetInput>({
  name: '',
  description: '',
  datasource: null,
  sql_text: '',
  target_folder: null,
  file_prefix: '',
  date_format: '%Y%m%d',
  keep_count: null,
  keep_days: null,
})

type ScheduleType = 'manual' | 'interval' | 'daily' | 'cron'
const schedule = reactive({ type: 'manual' as ScheduleType, interval: 60, time: '08:00', cron: '' })

function resetForm() {
  Object.assign(form, {
    name: '',
    description: '',
    datasource: null,
    sql_text: '',
    target_folder: null,
    file_prefix: '',
    date_format: '%Y%m%d',
    keep_count: null,
    keep_days: null,
  })
  Object.assign(schedule, { type: 'manual', interval: 60, time: '08:00', cron: '' })
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
  Object.assign(schedule, { type: 'manual', interval: 60, time: '08:00', cron: '' })
  if (row.cron) {
    const p = row.cron.trim().split(/\s+/)
    if (p.length === 5 && p[2] === '*' && p[3] === '*' && p[4] === '*' && /^\d+$/.test(p[0])) {
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
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Dataset) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    description: row.description,
    datasource: row.datasource,
    sql_text: row.sql_text,
    target_folder: row.target_folder,
    file_prefix: row.file_prefix,
    date_format: row.date_format,
    keep_count: row.keep_count,
    keep_days: row.keep_days,
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
    if (editingId.value) await updateDataset(editingId.value, payload)
    else await createDataset(payload)
    ElMessage.success('已保存')
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleRun(row: Dataset) {
  runningId.value = row.id
  try {
    const { data } = await runDataset(row.id)
    if (data.status === 'success') ElMessage.success(`运行成功，共 ${data.row_count} 行`)
    else ElMessage.error(`运行失败：${data.error_msg}`)
    await load()
  } finally {
    runningId.value = null
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

async function handleDownload(row: Dataset) {
  if (!row.last_run || row.last_run.status !== 'success') {
    ElMessage.warning('暂无可下载文件，请先运行')
    return
  }
  await downloadDataFile(row.last_run.id, `${row.name}.xlsx`)
}

async function handleDelete(row: Dataset) {
  await ElMessageBox.confirm(`确认删除数据集「${row.name}」？`, '提示', { type: 'warning' })
  await deleteDataset(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await Promise.all([
    load(),
    listDataSources().then((r) => (datasources.value = r.data)),
    listFolders().then((r) => (folders.value = r.data)),
  ])
})
</script>

<template>
  <PageContainer title="数据集" subtitle="写 SQL → 定时/手动跑 → 在目标文件夹新增带日期命名的文件">
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建数据集</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="datasource_name" label="数据源" min-width="100" />
        <el-table-column label="目标文件夹" min-width="120">
          <template #default="{ row }">{{ row.folder_name || '未指定' }}</template>
        </el-table-column>
        <el-table-column label="定时" min-width="110">
          <template #default="{ row }">{{ scheduleSummary(row) }}</template>
        </el-table-column>
        <el-table-column label="最近" min-width="110">
          <template #default="{ row }">
            <el-tag v-if="row.last_run?.status === 'success'" type="success" size="small">
              {{ row.last_run.row_count }} 行
            </el-tag>
            <el-tag v-else-if="row.last_run?.status === 'failed'" type="danger" size="small">
              失败
            </el-tag>
            <span v-else class="muted">未运行</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button
              text
              type="primary"
              :icon="VideoPlay"
              :loading="runningId === row.id"
              @click="handleRun(row)"
              >运行</el-button
            >
            <el-button text :icon="View" @click="handlePreview(row)">预览</el-button>
            <el-button text :icon="Download" @click="handleDownload(row)">下载</el-button>
            <el-button text :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button text type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty><el-empty description="还没有数据集" /></template>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑数据集' : '新建数据集'"
      width="660px"
    >
      <el-form label-width="84px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如：应收账款明细" />
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
        <el-form-item label="目标文件夹">
          <el-select
            v-model="form.target_folder"
            placeholder="文件存到哪个文件夹"
            clearable
            style="width: 100%"
          >
            <el-option v-for="f in folders" :key="f.id" :label="f.name" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="SQL" required>
          <el-input v-model="form.sql_text" type="textarea" :rows="6" placeholder="仅只读 SELECT" />
        </el-form-item>
        <el-form-item label="文件命名">
          <el-input v-model="form.file_prefix" placeholder="前缀(空=任务名)" style="width: 200px" />
          <span class="mx">_</span>
          <el-input v-model="form.date_format" placeholder="%Y%m%d" style="width: 130px" />
          <span class="mx">.xlsx</span>
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
          每 <el-input-number v-model="schedule.interval" :min="1" class="mx" /> 分钟
        </el-form-item>
        <el-form-item v-else-if="schedule.type === 'daily'" label=" ">
          每天
          <el-time-picker v-model="schedule.time" format="HH:mm" value-format="HH:mm" class="mx" />
        </el-form-item>
        <el-form-item v-else-if="schedule.type === 'cron'" label=" ">
          <el-input v-model="schedule.cron" placeholder="0 8 * * *" />
        </el-form-item>
        <el-form-item label="保留">
          最近 <el-input-number v-model="form.keep_count" :min="0" class="mx" /> 份 /
          <el-input-number v-model="form.keep_days" :min="0" class="mx" /> 天（空=全部保留）
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewVisible" title="数据预览（前 50 行）" width="80%">
      <div v-loading="previewLoading">
        <el-table v-if="preview?.ok" :data="preview.rows" border height="420" size="small">
          <el-table-column
            v-for="(col, i) in preview.columns"
            :key="i"
            :label="col"
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
