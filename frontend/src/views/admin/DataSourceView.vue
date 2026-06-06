<script setup lang="ts">
import { Connection, Delete, Edit, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import {
  type DataSource,
  type DataSourceInput,
  type TestResult,
  createDataSource,
  deleteDataSource,
  listDataSources,
  testDataSource,
  testDataSourceParams,
  updateDataSource,
} from '@/api/datasource'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const rows = ref<DataSource[]>([])

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const testing = ref(false)

const DEFAULT_PORT = { oracle: 1521, mysql: 3306 } as const

const form = reactive<DataSourceInput>({
  name: '',
  db_type: 'oracle',
  host: '',
  port: 1521,
  service_name: '',
  username: '',
  password: '',
})

// 切换数据库类型时套用默认端口（仅当端口仍是默认值时，避免覆盖用户填写）
function onDbTypeChange(t: 'oracle' | 'mysql') {
  const old = t === 'oracle' ? DEFAULT_PORT.mysql : DEFAULT_PORT.oracle
  if (form.port === old) form.port = DEFAULT_PORT[t]
}

function notify(result: TestResult) {
  if (result.ok) ElMessage.success(result.message)
  else ElMessage.error(result.message)
}

async function load() {
  loading.value = true
  try {
    const { data } = await listDataSources()
    rows.value = data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    db_type: 'oracle',
    host: '',
    port: 1521,
    service_name: '',
    username: '',
    password: '',
  })
  dialogVisible.value = true
}

function openEdit(row: DataSource) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    db_type: row.db_type,
    host: row.host,
    port: row.port,
    service_name: row.service_name,
    username: row.username,
    password: '', // 留空表示不修改
  })
  dialogVisible.value = true
}

async function handleTest() {
  testing.value = true
  try {
    const { data } = await testDataSourceParams({ ...form })
    notify(data)
  } finally {
    testing.value = false
  }
}

async function handleSave() {
  if (!form.name || !form.host || !form.service_name || !form.username) {
    ElMessage.warning('请填写名称、主机、服务名、账号')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateDataSource(editingId.value, { ...form })
      ElMessage.success('已更新')
    } else {
      await createDataSource({ ...form })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handleTestRow(row: DataSource) {
  const { data } = await testDataSource(row.id)
  notify(data)
}

async function handleDelete(row: DataSource) {
  await ElMessageBox.confirm(`确认删除数据源「${row.name}」？`, '提示', { type: 'warning' })
  await deleteDataSource(row.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <PageContainer title="数据源" subtitle="管理 Oracle 数据源连接（只读账号）">
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建数据源</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.db_type === 'mysql' ? 'warning' : ''" size="small">
              {{ row.db_type === 'mysql' ? 'MySQL' : 'Oracle' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="连接" min-width="220">
          <template #default="{ row }"
            >{{ row.host }}:{{ row.port }} / {{ row.service_name }}</template
          >
        </el-table-column>
        <el-table-column prop="username" label="账号" min-width="120" />
        <el-table-column label="密码" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.has_password" type="success" size="small">已设置</el-tag>
            <el-tag v-else type="info" size="small">未设置</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" :icon="Connection" @click="handleTestRow(row)">
              测试
            </el-button>
            <el-button text :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button text type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有数据源，点击右上角新建" />
        </template>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑数据源' : '新建数据源'"
      width="520px"
    >
      <el-form label-width="84px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如：财务库" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-radio-group v-model="form.db_type" @change="onDbTypeChange(form.db_type)">
            <el-radio-button value="oracle">Oracle</el-radio-button>
            <el-radio-button value="mysql">MySQL</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="主机" required>
          <el-input v-model="form.host" placeholder="IP 或域名" />
        </el-form-item>
        <el-form-item label="端口" required>
          <el-input-number v-model="form.port" :min="1" :max="65535" controls-position="right" />
        </el-form-item>
        <el-form-item :label="form.db_type === 'mysql' ? '数据库' : '服务名'" required>
          <el-input
            v-model="form.service_name"
            :placeholder="form.db_type === 'mysql' ? '数据库名 database' : 'service_name'"
          />
        </el-form-item>
        <el-form-item label="账号" required>
          <el-input v-model="form.username" placeholder="只读账号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="editingId ? '留空表示不修改' : '请输入密码'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :icon="Connection" :loading="testing" @click="handleTest">测试连接</el-button>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
</style>
