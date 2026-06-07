<script setup lang="ts">
import { Key, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { type PlatformUser, createUser, deleteUser, listUsers, updateUser } from '@/api/permission'
import PageContainer from '@/components/PageContainer.vue'

const users = ref<PlatformUser[]>([])
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

async function load() {
  loading.value = true
  try {
    users.value = (await listUsers()).data
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

onMounted(load)
</script>

<template>
  <PageContainer title="人员管理" subtitle="管理用户账号、角色与启停（部门归属在“部门管理”里配）">
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="createVisible = true">新建用户</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-table v-loading="loading" :data="users" stripe>
        <el-table-column label="账号" min-width="160">
          <template #default="{ row }">
            <div class="ucell">
              <div class="ava">{{ row.username.charAt(0).toUpperCase() }}</div>
              <span class="un">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="220">
          <template #default="{ row }">
            <el-tag v-for="t in roleTags(row)" :key="t.text" :type="t.type" size="small" class="rt">
              {{ t.text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span class="dot" :class="row.is_active ? 'ok' : 'off'" />
            {{ row.is_active ? '启用' : '停用' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" :icon="Key" @click="openRole(row)">角色/密码</el-button>
            <el-button text type="danger" :disabled="row.is_superuser" @click="handleDelete(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

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

    <el-dialog v-model="roleVisible" :title="`角色 · ${roleUser?.username}`" width="400px">
      <el-form label-width="110px">
        <el-form-item label="辅助管理员">
          <el-switch v-model="roleForm.is_assistant_admin" />
        </el-form-item>
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
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
}
.ucell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.ava {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--accent-weak);
  color: var(--accent);
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.un {
  font-weight: 550;
}
.rt {
  margin-right: 6px;
}
.dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-right: 5px;
  vertical-align: middle;
}
.dot.ok {
  background: var(--success);
}
.dot.off {
  background: var(--ink-3);
}
</style>
