<script setup lang="ts">
import { Delete, EditPen, FolderAdd, Plus, Share } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import {
  type Department,
  type Folder,
  type FolderShare,
  createDepartment,
  createFolder,
  createFolderShare,
  deleteFolder,
  deleteFolderShare,
  listDepartments,
  listFolderShares,
  listFolders,
  updateFolder,
} from '@/api/catalog'
import { type PlatformUser, listUsers } from '@/api/permission'
import PageContainer from '@/components/PageContainer.vue'

interface TreeNode {
  id: number
  name: string
  parent: number | null
  children: TreeNode[]
}

const loading = ref(false)
const treeData = ref<TreeNode[]>([])
const departments = ref<Department[]>([])
const users = ref<PlatformUser[]>([])

const shareVisible = ref(false)
const shareFolder = ref<TreeNode | null>(null)
const shares = ref<FolderShare[]>([])
const shareType = ref<'dept' | 'user'>('dept')
const shareDept = ref<number | null>(null)
const shareUser = ref<number | null>(null)

function buildTree(flat: Folder[]): TreeNode[] {
  const map = new Map<number, TreeNode>()
  flat.forEach((f) => map.set(f.id, { id: f.id, name: f.name, parent: f.parent, children: [] }))
  const roots: TreeNode[] = []
  map.forEach((node) => {
    if (node.parent && map.has(node.parent)) map.get(node.parent)!.children.push(node)
    else roots.push(node)
  })
  return roots
}

async function load() {
  loading.value = true
  try {
    treeData.value = buildTree((await listFolders()).data)
  } finally {
    loading.value = false
  }
}

async function addRoot() {
  const name = await prompt('新建根文件夹')
  if (name) {
    await createFolder(name, null)
    await load()
  }
}

async function addChild(node: TreeNode) {
  const name = await prompt('新建子文件夹')
  if (name) {
    await createFolder(name, node.id)
    await load()
  }
}

async function rename(node: TreeNode) {
  const name = await prompt('重命名', node.name)
  if (name && name !== node.name) {
    await updateFolder(node.id, { name })
    await load()
  }
}

async function remove(node: TreeNode) {
  await ElMessageBox.confirm(`删除「${node.name}」及其所有子文件夹与文件？`, '提示', {
    type: 'warning',
  })
  await deleteFolder(node.id)
  ElMessage.success('已删除')
  await load()
}

async function prompt(title: string, value = ''): Promise<string | null> {
  try {
    const { value: v } = await ElMessageBox.prompt('请输入名称', title, { inputValue: value })
    return (v ?? '').trim() || null
  } catch {
    return null
  }
}

// 拖拽移动（成环由后端拒绝）
async function onDrop(
  dragging: { data: TreeNode },
  drop: { data: TreeNode },
  type: 'inner' | 'before' | 'after',
) {
  const parent = type === 'inner' ? drop.data.id : drop.data.parent
  try {
    await updateFolder(dragging.data.id, { parent })
    ElMessage.success('已移动')
  } catch {
    // 后端拒绝成环等，回滚
  }
  await load()
}

// 授权
async function openShare(node: TreeNode) {
  shareFolder.value = node
  shareType.value = 'dept'
  shareDept.value = null
  shareUser.value = null
  shareVisible.value = true
  shares.value = (await listFolderShares(node.id)).data
}
async function addShare() {
  if (!shareFolder.value) return
  const data: { folder: number; subject_department?: number; subject_user?: number } = {
    folder: shareFolder.value.id,
  }
  if (shareType.value === 'dept') {
    if (!shareDept.value) return ElMessage.warning('请选择部门')
    data.subject_department = shareDept.value
  } else {
    if (!shareUser.value) return ElMessage.warning('请选择用户')
    data.subject_user = shareUser.value
  }
  await createFolderShare(data)
  shares.value = (await listFolderShares(shareFolder.value.id)).data
}
async function removeShare(id: number) {
  await deleteFolderShare(id)
  if (shareFolder.value) shares.value = (await listFolderShares(shareFolder.value.id)).data
}

async function addDepartmentQuick() {
  const name = await prompt('新建部门')
  if (name) {
    await createDepartment(name)
    departments.value = (await listDepartments()).data
    ElMessage.success('已新建部门')
  }
}

onMounted(async () => {
  await Promise.all([
    load(),
    listDepartments().then((r) => (departments.value = r.data)),
    listUsers().then((r) => (users.value = r.data)),
  ])
})
</script>

<template>
  <PageContainer title="文件夹" subtitle="管理目录树（拖拽移动）并授权给部门或个人">
    <template #actions>
      <el-button :icon="FolderAdd" @click="addRoot">新建根文件夹</el-button>
    </template>

    <el-card class="card" shadow="never">
      <el-tree
        v-loading="loading"
        :data="treeData"
        node-key="id"
        draggable
        :expand-on-click-node="false"
        default-expand-all
        @node-drop="onDrop"
      >
        <template #default="{ data }">
          <span class="node">
            <span class="nm">{{ data.name }}</span>
            <span class="ops">
              <el-button text :icon="Plus" title="新建子文件夹" @click.stop="addChild(data)" />
              <el-button text :icon="EditPen" title="重命名" @click.stop="rename(data)" />
              <el-button text :icon="Share" title="授权" @click.stop="openShare(data)" />
              <el-button
                text
                type="danger"
                :icon="Delete"
                title="删除"
                @click.stop="remove(data)"
              />
            </span>
          </span>
        </template>
      </el-tree>
      <el-empty v-if="!treeData.length && !loading" description="还没有文件夹" />
    </el-card>

    <el-dialog v-model="shareVisible" :title="`授权 · ${shareFolder?.name}`" width="520px">
      <el-table :data="shares" size="small" border>
        <el-table-column label="授权对象">
          <template #default="{ row }">
            <el-tag v-if="row.subject_department" type="success" size="small">
              部门：{{ row.department_name }}
            </el-tag>
            <el-tag v-else size="small">个人：{{ row.username }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column width="60">
          <template #default="{ row }">
            <el-button text type="danger" :icon="Delete" @click="removeShare(row.id)" />
          </template>
        </el-table-column>
        <template #empty><span class="muted">还没有授权</span></template>
      </el-table>
      <div class="addrow">
        <el-radio-group v-model="shareType">
          <el-radio-button value="dept">部门</el-radio-button>
          <el-radio-button value="user">个人</el-radio-button>
        </el-radio-group>
        <el-select
          v-if="shareType === 'dept'"
          v-model="shareDept"
          placeholder="选择部门"
          style="width: 180px"
        >
          <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-select v-else v-model="shareUser" placeholder="选择用户" style="width: 180px">
          <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="addShare">授权</el-button>
      </div>
      <el-button v-if="shareType === 'dept'" text type="primary" @click="addDepartmentQuick">
        + 没有部门？快速新建
      </el-button>
    </el-dialog>
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  min-height: 360px;
}
.node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}
.ops {
  opacity: 0;
  transition: opacity 0.15s;
}
.node:hover .ops {
  opacity: 1;
}
.addrow {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}
.muted {
  color: var(--app-text-secondary);
}
</style>
