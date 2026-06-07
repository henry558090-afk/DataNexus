<script setup lang="ts">
import { Delete, Key, OfficeBuilding, Plus, User as UserIcon } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { type Department, createDepartment, deleteDepartment, listDepartments } from '@/api/catalog'
import {
  type Membership,
  type PlatformUser,
  createMembership,
  createUser,
  deleteMembership,
  deleteUser,
  listMemberships,
  listUsers,
  updateUser,
} from '@/api/permission'
import PageContainer from '@/components/PageContainer.vue'

const users = ref<PlatformUser[]>([])
const departments = ref<Department[]>([])
const loading = ref(false)

const createVisible = ref(false)
const newUser = reactive({ username: '', password: '' })

const roleVisible = ref(false)
const roleUser = ref<PlatformUser | null>(null)
const roleForm = reactive({
  is_assistant_admin: false,
  is_boss: false,
  is_active: true,
  password: '',
})

const deptVisible = ref(false)
const deptUser = ref<PlatformUser | null>(null)
const memberships = ref<Membership[]>([])
const addDeptId = ref<number | null>(null)

const newDeptName = ref('')

async function loadAll() {
  loading.value = true
  try {
    users.value = (await listUsers()).data
    departments.value = (await listDepartments()).data
  } finally {
    loading.value = false
  }
}

function roleTags(u: PlatformUser) {
  const t: { text: string; type: 'danger' | 'warning' | 'success' | 'info' }[] = []
  if (u.is_superuser) t.push({ text: '超级管理员', type: 'danger' })
  if (u.is_assistant_admin) t.push({ text: '辅助管理员', type: 'warning' })
  if (u.is_boss) t.push({ text: '老板', type: 'success' })
  if (!t.length) t.push({ text: '普通用户', type: 'info' })
  return t
}

async function handleCreate() {
  if (!newUser.username || !newUser.password) return ElMessage.warning('请输入账号和密码')
  await createUser({ ...newUser })
  ElMessage.success('已创建')
  createVisible.value = false
  newUser.username = ''
  newUser.password = ''
  await loadAll()
}

function openRole(u: PlatformUser) {
  roleUser.value = u
  Object.assign(roleForm, {
    is_assistant_admin: u.is_assistant_admin,
    is_boss: u.is_boss,
    is_active: u.is_active,
    password: '',
  })
  roleVisible.value = true
}
async function saveRole() {
  if (!roleUser.value) return
  await updateUser(roleUser.value.id, { ...roleForm })
  ElMessage.success('已保存')
  roleVisible.value = false
  await loadAll()
}

async function handleDelete(u: PlatformUser) {
  await ElMessageBox.confirm(`确认删除用户「${u.username}」？`, '提示', { type: 'warning' })
  await deleteUser(u.id)
  ElMessage.success('已删除')
  await loadAll()
}

async function openDept(u: PlatformUser) {
  deptUser.value = u
  addDeptId.value = null
  deptVisible.value = true
  memberships.value = (await listMemberships(u.id)).data
}
async function addMembership() {
  if (!deptUser.value || !addDeptId.value) return ElMessage.warning('请选择部门')
  await createMembership({ user: deptUser.value.id, department: addDeptId.value })
  addDeptId.value = null
  memberships.value = (await listMemberships(deptUser.value.id)).data
}
async function removeMembership(id: number) {
  await deleteMembership(id)
  if (deptUser.value) memberships.value = (await listMemberships(deptUser.value.id)).data
}

async function addDept() {
  if (!newDeptName.value.trim()) return
  await createDepartment(newDeptName.value.trim())
  newDeptName.value = ''
  departments.value = (await listDepartments()).data
}
async function removeDept(d: Department) {
  await ElMessageBox.confirm(`删除部门「${d.name}」？`, '提示', { type: 'warning' })
  await deleteDepartment(d.id)
  departments.value = (await listDepartments()).data
}

onMounted(loadAll)
</script>

<template>
  <PageContainer
    title="用户与部门"
    subtitle="管理用户角色、部门归属（部门=用户组，用于文件夹授权）"
  >
    <el-row :gutter="16">
      <el-col :span="16">
        <el-card class="card" shadow="never">
          <template #header>
            <div class="head">
              <span
                ><el-icon><UserIcon /></el-icon> 用户</span
              >
              <el-button type="primary" size="small" :icon="Plus" @click="createVisible = true">
                新建用户
              </el-button>
            </div>
          </template>
          <el-table v-loading="loading" :data="users" stripe>
            <el-table-column prop="username" label="账号" min-width="120" />
            <el-table-column label="角色" min-width="200">
              <template #default="{ row }">
                <el-tag
                  v-for="t in roleTags(row)"
                  :key="t.text"
                  :type="t.type"
                  size="small"
                  class="rt"
                  >{{ t.text }}</el-tag
                >
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button text type="primary" :icon="Key" @click="openRole(row)">角色</el-button>
                <el-button text :icon="OfficeBuilding" @click="openDept(row)">部门</el-button>
                <el-button
                  text
                  type="danger"
                  :icon="Delete"
                  :disabled="row.is_superuser"
                  @click="handleDelete(row)"
                  >删除</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="card" shadow="never">
          <template #header
            ><span
              ><el-icon><OfficeBuilding /></el-icon> 部门</span
            ></template
          >
          <div class="addrow">
            <el-input
              v-model="newDeptName"
              size="small"
              placeholder="新部门名"
              @keyup.enter="addDept"
            />
            <el-button size="small" type="primary" :icon="Plus" @click="addDept" />
          </div>
          <div v-for="d in departments" :key="d.id" class="item">
            <span>{{ d.name }}</span>
            <el-button text type="danger" :icon="Delete" @click="removeDept(d)" />
          </div>
          <el-empty v-if="!departments.length" description="还没有部门" :image-size="50" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建用户 -->
    <el-dialog v-model="createVisible" title="新建用户" width="400px">
      <el-form label-width="60px">
        <el-form-item label="账号" required><el-input v-model="newUser.username" /></el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="newUser.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 角色 -->
    <el-dialog v-model="roleVisible" :title="`角色 · ${roleUser?.username}`" width="400px">
      <el-form label-width="100px">
        <el-form-item label="辅助管理员"
          ><el-switch v-model="roleForm.is_assistant_admin"
        /></el-form-item>
        <el-form-item label="老板(看全部)"><el-switch v-model="roleForm.is_boss" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="roleForm.is_active" /></el-form-item>
        <el-form-item label="重置密码">
          <el-input
            v-model="roleForm.password"
            type="password"
            show-password
            placeholder="留空不改"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>

    <!-- 部门归属 -->
    <el-dialog v-model="deptVisible" :title="`部门 · ${deptUser?.username}`" width="480px">
      <el-table :data="memberships" size="small" border>
        <el-table-column prop="department_name" label="所属部门" />
        <el-table-column width="60">
          <template #default="{ row }">
            <el-button text type="danger" :icon="Delete" @click="removeMembership(row.id)" />
          </template>
        </el-table-column>
        <template #empty><span class="muted">未加入任何部门</span></template>
      </el-table>
      <div class="addrow2">
        <el-select v-model="addDeptId" placeholder="选择部门加入" style="width: 240px">
          <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="addMembership">加入</el-button>
      </div>
    </el-dialog>
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.rt {
  margin-right: 6px;
}
.addrow {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.addrow2 {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}
.item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 4px;
}
.muted {
  color: var(--app-text-secondary);
}
</style>
