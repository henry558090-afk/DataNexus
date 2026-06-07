<script setup lang="ts">
import { Folder, FolderOpened, OfficeBuilding, User as UserIcon } from '@element-plus/icons-vue'
import type { ElTree } from 'element-plus'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import {
  type Department,
  type Folder as FolderModel,
  createFolderShare,
  deleteFolderShare,
  listDepartments,
  listFolders,
  listSharesByDept,
  listSharesByUser,
} from '@/api/catalog'
import { type PlatformUser, listUsers } from '@/api/permission'
import PageContainer from '@/components/PageContainer.vue'

interface TreeNode {
  id: number
  name: string
  parent: number | null
  children: TreeNode[]
}
interface Subject {
  type: 'dept' | 'user'
  id: number
  name: string
}

const tab = ref<'dept' | 'user'>('dept')
const departments = ref<Department[]>([])
const users = ref<PlatformUser[]>([])
const treeData = ref<TreeNode[]>([])
const treeRef = ref<InstanceType<typeof ElTree>>()

const subject = ref<Subject | null>(null)
const shareMap = ref<Record<number, number>>({}) // folderId -> shareId
const loadingShares = ref(false)
const syncing = ref(false)

function buildTree(flat: FolderModel[]): TreeNode[] {
  const map = new Map<number, TreeNode>()
  flat.forEach((f) => map.set(f.id, { id: f.id, name: f.name, parent: f.parent, children: [] }))
  const roots: TreeNode[] = []
  map.forEach((n) => {
    if (n.parent && map.has(n.parent)) map.get(n.parent)!.children.push(n)
    else roots.push(n)
  })
  return roots
}

async function selectSubject(s: Subject) {
  subject.value = s
  loadingShares.value = true
  try {
    const shares = (s.type === 'dept' ? await listSharesByDept(s.id) : await listSharesByUser(s.id))
      .data
    const map: Record<number, number> = {}
    shares.forEach((sh) => (map[sh.folder] = sh.id))
    shareMap.value = map
    syncing.value = true
    treeRef.value?.setCheckedKeys(Object.keys(map).map(Number), false)
    syncing.value = false
  } finally {
    loadingShares.value = false
  }
}

async function onCheck(_data: TreeNode, info: { checkedKeys: number[] }) {
  if (syncing.value || !subject.value) return
  const checked = new Set(info.checkedKeys)
  const current = new Set(Object.keys(shareMap.value).map(Number))
  // 新增
  for (const fid of checked) {
    if (!current.has(fid)) {
      const payload =
        subject.value.type === 'dept'
          ? { folder: fid, subject_department: subject.value.id }
          : { folder: fid, subject_user: subject.value.id }
      const { data } = await createFolderShare(payload)
      shareMap.value[fid] = data.id
    }
  }
  // 移除
  for (const fid of current) {
    if (!checked.has(fid)) {
      await deleteFolderShare(shareMap.value[fid])
      delete shareMap.value[fid]
    }
  }
  ElMessage.success({ message: '已更新权限', duration: 900 })
}

onMounted(async () => {
  const [d, u, f] = await Promise.all([listDepartments(), listUsers(), listFolders()])
  departments.value = d.data
  users.value = u.data
  treeData.value = buildTree(f.data)
})
</script>

<template>
  <PageContainer
    title="权限管理"
    subtitle="选择人或部门，勾选 TA 能看的文件夹 · 授权自动包含子文件夹 · 最细到人"
  >
    <div class="perm">
      <!-- 左：主体 -->
      <aside class="subjects">
        <div class="seg">
          <button :class="{ on: tab === 'dept' }" @click="tab = 'dept'">
            <el-icon><OfficeBuilding /></el-icon> 部门
          </button>
          <button :class="{ on: tab === 'user' }" @click="tab = 'user'">
            <el-icon><UserIcon /></el-icon> 人员
          </button>
        </div>
        <div class="slist">
          <template v-if="tab === 'dept'">
            <button
              v-for="d in departments"
              :key="'d' + d.id"
              class="sitem"
              :class="{ on: subject?.type === 'dept' && subject.id === d.id }"
              @click="selectSubject({ type: 'dept', id: d.id, name: d.name })"
            >
              <el-icon><OfficeBuilding /></el-icon><span>{{ d.name }}</span>
            </button>
            <el-empty v-if="!departments.length" description="还没有部门" :image-size="46" />
          </template>
          <template v-else>
            <button
              v-for="u in users"
              :key="'u' + u.id"
              class="sitem"
              :class="{ on: subject?.type === 'user' && subject.id === u.id }"
              @click="selectSubject({ type: 'user', id: u.id, name: u.username })"
            >
              <el-icon><UserIcon /></el-icon><span>{{ u.username }}</span>
            </button>
          </template>
        </div>
      </aside>

      <!-- 右：文件夹勾选 -->
      <section class="grant">
        <div v-if="subject" class="grant-head">
          <span class="muted">配置可见文件夹 ·</span>
          <strong>{{ subject.name }}</strong>
          <el-tag size="small" :type="subject.type === 'dept' ? 'success' : 'info'">
            {{ subject.type === 'dept' ? '部门' : '个人' }}
          </el-tag>
        </div>
        <div class="grant-body" v-loading="loadingShares">
          <el-tree
            v-show="subject"
            ref="treeRef"
            :data="treeData"
            node-key="id"
            show-checkbox
            check-strictly
            :props="{ label: 'name', children: 'children' }"
            :expand-on-click-node="false"
            default-expand-all
            @check="onCheck"
          >
            <template #default="{ node, data }">
              <span class="tnode">
                <el-icon class="ti">
                  <FolderOpened v-if="node.expanded && data.children.length" />
                  <Folder v-else />
                </el-icon>
                {{ data.name }}
              </span>
            </template>
          </el-tree>
          <div v-if="!subject" class="hint">
            <el-icon :size="28"><OfficeBuilding /></el-icon>
            <p>从左侧选择一个人或部门</p>
            <span>再勾选 TA 能查看的文件夹</span>
          </div>
        </div>
      </section>
    </div>
  </PageContainer>
</template>

<style scoped>
.perm {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 16px;
  min-height: 560px;
}
.subjects,
.grant {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.seg {
  display: flex;
  gap: 4px;
  padding: 12px;
  border-bottom: 1px solid var(--border);
}
.seg button {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  border: none;
  background: var(--surface-2);
  color: var(--ink-2);
  border-radius: var(--r-sm);
  font-size: 13px;
  font-weight: 550;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.seg button.on {
  background: var(--accent);
  color: #fff;
}
.slist {
  flex: 1;
  overflow: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sitem {
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
  text-align: left;
  transition: background var(--dur-fast) var(--ease-out);
}
.sitem :deep(.el-icon) {
  color: var(--ink-3);
}
.sitem:hover {
  background: var(--surface-2);
}
.sitem.on {
  background: var(--accent-weak);
  color: var(--accent);
  font-weight: 600;
}
.sitem.on :deep(.el-icon) {
  color: var(--accent);
}
.grant-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}
.grant-body {
  flex: 1;
  padding: 14px 18px;
  overflow: auto;
}
.tnode {
  display: flex;
  align-items: center;
  gap: 7px;
}
.ti {
  color: var(--accent);
}
.muted {
  color: var(--ink-3);
}
.hint {
  height: 100%;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--ink-3);
  text-align: center;
}
.hint p {
  margin: 12px 0 2px;
  color: var(--ink-2);
  font-size: 14px;
}
.hint span {
  font-size: 12px;
}
.grant-body :deep(.el-tree-node__content) {
  height: 36px;
  border-radius: var(--r-sm);
}
</style>
