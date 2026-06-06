<script setup lang="ts">
import { Delete, Key, Lock, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { type Category, type Department, listCategories, listDepartments } from '@/api/catalog'
import {
  type Membership,
  type PlatformUser,
  createGrant,
  createMembership,
  createUser,
  deleteGrant,
  deleteMembership,
  deleteUser,
  listGrants,
  listMemberships,
  listUsers,
  updateUser,
} from '@/api/permission'
import PageContainer from '@/components/PageContainer.vue'

const ROLE_LABELS: Record<string, string> = {
  director: '总监',
  manager: '部门主管',
  member: '成员',
}

const loading = ref(false)
const users = ref<PlatformUser[]>([])
const departments = ref<Department[]>([])
const categories = ref<Category[]>([])

// 新建用户
const createVisible = ref(false)
const newUser = reactive({ username: '', password: '' })

// 角色
const roleVisible = ref(false)
const roleUser = ref<PlatformUser | null>(null)
const roleForm = reactive({
  is_assistant_admin: false,
  is_boss: false,
  is_active: true,
  password: '',
})

// 可见权限
const permVisible = ref(false)
const permUser = ref<PlatformUser | null>(null)
const memberships = ref<Membership[]>([])
const grants = ref<{ id: number; category: number | null }[]>([])
const newMember = reactive({
  department: null as number | null,
  role: 'member',
  see_all_in_dept: false,
})
const newGrantCat = ref<number | null>(null)

async function load() {
  loading.value = true
  try {
    users.value = (await listUsers()).data
  } finally {
    loading.value = false
  }
}

function roleTags(
  u: PlatformUser,
): { text: string; type: 'danger' | 'warning' | 'success' | 'info' }[] {
  const tags: { text: string; type: 'danger' | 'warning' | 'success' | 'info' }[] = []
  if (u.is_superuser) tags.push({ text: '超级管理员', type: 'danger' })
  if (u.is_assistant_admin) tags.push({ text: '辅助管理员', type: 'warning' })
  if (u.is_boss) tags.push({ text: '老板', type: 'success' })
  if (!tags.length) tags.push({ text: '普通用户', type: 'info' })
  return tags
}

async function handleCreate() {
  if (!newUser.username || !newUser.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  await createUser({ ...newUser })
  ElMessage.success('已创建用户')
  createVisible.value = false
  newUser.username = ''
  newUser.password = ''
  await load()
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
  await load()
}

async function handleDelete(u: PlatformUser) {
  await ElMessageBox.confirm(`确认删除用户「${u.username}」？`, '提示', { type: 'warning' })
  await deleteUser(u.id)
  ElMessage.success('已删除')
  await load()
}

async function openPerm(u: PlatformUser) {
  permUser.value = u
  permVisible.value = true
  newMember.department = null
  newMember.role = 'member'
  newMember.see_all_in_dept = false
  newGrantCat.value = null
  await refreshPerm()
}

async function refreshPerm() {
  if (!permUser.value) return
  memberships.value = (await listMemberships(permUser.value.id)).data
  grants.value = (await listGrants(permUser.value.id)).data
}

async function addMembership() {
  if (!permUser.value || !newMember.department) {
    ElMessage.warning('请选择部门')
    return
  }
  await createMembership({
    user: permUser.value.id,
    ...newMember,
    department: newMember.department,
  })
  await refreshPerm()
}

async function removeMembership(id: number) {
  await deleteMembership(id)
  await refreshPerm()
}

async function addGrant() {
  if (!permUser.value || !newGrantCat.value) {
    ElMessage.warning('请选择分类')
    return
  }
  await createGrant({ subject_user: permUser.value.id, category: newGrantCat.value })
  newGrantCat.value = null
  await refreshPerm()
}

async function removeGrant(id: number) {
  await deleteGrant(id)
  await refreshPerm()
}

function catLabel(id: number | null): string {
  const c = categories.value.find((x) => x.id === id)
  return c ? `${c.department_name} / ${c.name}` : `#${id}`
}

onMounted(async () => {
  await Promise.all([
    load(),
    listDepartments().then((r) => (departments.value = r.data)),
    listCategories().then((r) => (categories.value = r.data)),
  ])
})
</script>

<template>
  <PageContainer title="用户与权限" subtitle="角色分配（老板/总监/主管/成员）与授权">
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="createVisible = true">新建用户</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="users" stripe>
        <el-table-column prop="username" label="账号" min-width="140" />
        <el-table-column label="角色" min-width="240">
          <template #default="{ row }">
            <el-tag v-for="t in roleTags(row)" :key="t.text" :type="t.type" size="small" class="rt">
              {{ t.text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" :icon="Key" @click="openRole(row)">角色</el-button>
            <el-button text :icon="Lock" @click="openPerm(row)">可见权限</el-button>
            <el-button
              text
              type="danger"
              :icon="Delete"
              :disabled="row.is_superuser"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建用户 -->
    <el-dialog v-model="createVisible" title="新建用户" width="420px">
      <el-form label-width="64px">
        <el-form-item label="账号" required>
          <el-input v-model="newUser.username" />
        </el-form-item>
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
    <el-dialog v-model="roleVisible" :title="`角色 · ${roleUser?.username}`" width="420px">
      <el-form label-width="100px">
        <el-form-item label="辅助管理员">
          <el-switch v-model="roleForm.is_assistant_admin" />
        </el-form-item>
        <el-form-item label="老板(看全部)">
          <el-switch v-model="roleForm.is_boss" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="roleForm.is_active" />
        </el-form-item>
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

    <!-- 可见权限 -->
    <el-dialog v-model="permVisible" :title="`可见权限 · ${permUser?.username}`" width="640px">
      <h4 class="sec">部门成员</h4>
      <el-table :data="memberships" size="small" border>
        <el-table-column prop="department_name" label="部门" />
        <el-table-column label="角色">
          <template #default="{ row }">{{ ROLE_LABELS[row.role] ?? row.role }}</template>
        </el-table-column>
        <el-table-column label="看本部门全部" width="120">
          <template #default="{ row }">{{ row.see_all_in_dept ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column width="70">
          <template #default="{ row }">
            <el-button text type="danger" :icon="Delete" @click="removeMembership(row.id)" />
          </template>
        </el-table-column>
      </el-table>
      <div class="addrow">
        <el-select v-model="newMember.department" placeholder="部门" style="width: 160px">
          <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-select v-model="newMember.role" style="width: 120px">
          <el-option label="总监" value="director" />
          <el-option label="部门主管" value="manager" />
          <el-option label="成员" value="member" />
        </el-select>
        <span class="lbl">看本部门全部</span>
        <el-switch v-model="newMember.see_all_in_dept" />
        <el-button type="primary" :icon="Plus" @click="addMembership">添加</el-button>
      </div>

      <h4 class="sec">按分类授权（成员可见）</h4>
      <el-table :data="grants" size="small" border>
        <el-table-column label="分类">
          <template #default="{ row }">{{ catLabel(row.category) }}</template>
        </el-table-column>
        <el-table-column width="70">
          <template #default="{ row }">
            <el-button text type="danger" :icon="Delete" @click="removeGrant(row.id)" />
          </template>
        </el-table-column>
      </el-table>
      <div class="addrow">
        <el-select v-model="newGrantCat" placeholder="选择分类" style="width: 280px">
          <el-option
            v-for="c in categories"
            :key="c.id"
            :label="`${c.department_name} / ${c.name}`"
            :value="c.id"
          />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="addGrant">授权</el-button>
      </div>

      <template #footer>
        <el-button @click="permVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
}
.rt {
  margin-right: 6px;
}
.sec {
  margin: 16px 0 8px;
  font-size: 14px;
  font-weight: 700;
}
.addrow {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}
.lbl {
  font-size: 13px;
  color: var(--app-text-secondary);
}
</style>
