<script setup lang="ts">
import { Delete, OfficeBuilding, Plus, User as UserIcon } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { type Department, createDepartment, deleteDepartment, listDepartments } from '@/api/catalog'
import {
  type Membership,
  type PlatformUser,
  createMembership,
  deleteMembership,
  listMembershipsByDept,
  listUsers,
} from '@/api/permission'
import PageContainer from '@/components/PageContainer.vue'

const departments = ref<Department[]>([])
const users = ref<PlatformUser[]>([])
const selected = ref<Department | null>(null)
const members = ref<Membership[]>([])
const addUserId = ref<number | null>(null)
const loadingMembers = ref(false)

async function loadDepts() {
  departments.value = (await listDepartments()).data
}

async function selectDept(d: Department) {
  selected.value = d
  addUserId.value = null
  loadingMembers.value = true
  try {
    members.value = (await listMembershipsByDept(d.id)).data
  } finally {
    loadingMembers.value = false
  }
}

async function addDept() {
  try {
    const { value } = await ElMessageBox.prompt('请输入部门名称', '新建部门', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
    })
    const name = (value ?? '').trim()
    if (!name) return
    await createDepartment(name)
    await loadDepts()
    ElMessage.success('已新建部门')
  } catch {
    /* 取消 */
  }
}

async function removeDept(d: Department) {
  await ElMessageBox.confirm(
    `删除部门「${d.name}」？该部门的成员归属与文件夹授权一并移除。`,
    '提示',
    {
      type: 'warning',
    },
  )
  await deleteDepartment(d.id)
  if (selected.value?.id === d.id) selected.value = null
  await loadDepts()
  ElMessage.success('已删除')
}

async function addMember() {
  if (!selected.value || !addUserId.value) return ElMessage.warning('请选择用户')
  await createMembership({ user: addUserId.value, department: selected.value.id })
  addUserId.value = null
  members.value = (await listMembershipsByDept(selected.value.id)).data
  ElMessage.success('已加入')
}

async function removeMember(m: Membership) {
  await deleteMembership(m.id)
  if (selected.value) members.value = (await listMembershipsByDept(selected.value.id)).data
}

onMounted(async () => {
  await Promise.all([loadDepts(), listUsers().then((r) => (users.value = r.data))])
})
</script>

<template>
  <PageContainer title="部门管理" subtitle="部门 = 用户组，用于在权限管理里按部门授权文件夹">
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="addDept">新建部门</el-button>
    </template>

    <div class="dept">
      <aside class="list">
        <div class="list-head">全部部门 · {{ departments.length }}</div>
        <div class="items">
          <button
            v-for="d in departments"
            :key="d.id"
            class="item"
            :class="{ on: selected?.id === d.id }"
            @click="selectDept(d)"
          >
            <el-icon><OfficeBuilding /></el-icon>
            <span class="nm">{{ d.name }}</span>
            <el-icon class="del" @click.stop="removeDept(d)"><Delete /></el-icon>
          </button>
          <el-empty v-if="!departments.length" description="还没有部门" :image-size="50" />
        </div>
      </aside>

      <section class="members">
        <template v-if="selected">
          <div class="m-head">
            <span
              ><strong>{{ selected.name }}</strong> 的成员 · {{ members.length }}</span
            >
            <div class="add">
              <el-select
                v-model="addUserId"
                placeholder="选择用户加入"
                filterable
                style="width: 200px"
              >
                <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
              </el-select>
              <el-button type="primary" :icon="Plus" @click="addMember">加入</el-button>
            </div>
          </div>
          <div class="m-body" v-loading="loadingMembers">
            <div v-for="m in members" :key="m.id" class="member rise-in">
              <div class="ava">{{ m.username.charAt(0).toUpperCase() }}</div>
              <span class="u">{{ m.username }}</span>
              <el-button text type="danger" :icon="Delete" @click="removeMember(m)">移出</el-button>
            </div>
            <div v-if="!members.length && !loadingMembers" class="empty">
              <el-icon :size="26"><UserIcon /></el-icon>
              <p>这个部门还没有成员</p>
              <span>从上方选择用户加入</span>
            </div>
          </div>
        </template>
        <div v-else class="hint">
          <el-icon :size="28"><OfficeBuilding /></el-icon>
          <p>从左侧选择一个部门</p>
          <span>查看并管理它的成员</span>
        </div>
      </section>
    </div>
  </PageContainer>
</template>

<style scoped>
.dept {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  min-height: 540px;
}
.list,
.members {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.list-head,
.m-head {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  color: var(--ink-2);
}
.m-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.add {
  display: flex;
  gap: 8px;
}
.items {
  flex: 1;
  overflow: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: var(--r-sm);
  font-size: 14px;
  color: var(--ink);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}
.item > .el-icon:first-child {
  color: var(--ink-3);
}
.item .nm {
  flex: 1;
  text-align: left;
}
.item .del {
  opacity: 0;
  color: var(--danger);
}
.item:hover {
  background: var(--surface-2);
}
.item:hover .del {
  opacity: 1;
}
.item.on {
  background: var(--accent-weak);
  color: var(--accent);
  font-weight: 600;
}
.item.on > .el-icon:first-child {
  color: var(--accent);
}
.m-body {
  flex: 1;
  overflow: auto;
  padding: 10px;
}
.member {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--r);
  transition: background var(--dur-fast) var(--ease-out);
}
.member:hover {
  background: var(--surface-2);
}
.ava {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent-weak);
  color: var(--accent);
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.member .u {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}
.hint,
.empty {
  height: 100%;
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--ink-3);
  text-align: center;
}
.hint p,
.empty p {
  margin: 12px 0 2px;
  color: var(--ink-2);
  font-size: 14px;
}
.hint span,
.empty span {
  font-size: 12px;
}
</style>
