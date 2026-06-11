<script setup lang="ts">
import { Delete, Document, EditPen, FolderAdd, FolderOpened, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

import { type Folder, createFolder, deleteFolder, listFolders, updateFolder } from '@/api/catalog'
import { type Dataset, listDatasets, updateDataset } from '@/api/dataset'
import PageContainer from '@/components/PageContainer.vue'

interface TreeNode {
  id: number
  name: string
  parent: number | null
  requestable: boolean
  children: TreeNode[]
}

const loading = ref(false)
const treeData = ref<TreeNode[]>([])
const datasets = ref<Dataset[]>([])
const selected = ref<TreeNode | null>(null)
const mountVisible = ref(false)
const mountPick = ref<number | null>(null)

const mounted = computed(() =>
  selected.value ? datasets.value.filter((d) => d.target_folder === selected.value!.id) : [],
)
const mountable = computed(() =>
  datasets.value.filter((d) => d.target_folder !== selected.value?.id),
)

function buildTree(flat: Folder[]): TreeNode[] {
  const map = new Map<number, TreeNode>()
  flat.forEach((f) =>
    map.set(f.id, {
      id: f.id,
      name: f.name,
      parent: f.parent,
      requestable: f.requestable,
      children: [],
    }),
  )
  const roots: TreeNode[] = []
  map.forEach((n) => {
    if (n.parent && map.has(n.parent)) map.get(n.parent)!.children.push(n)
    else roots.push(n)
  })
  return roots
}

async function load() {
  loading.value = true
  try {
    const [f, d] = await Promise.all([listFolders(), listDatasets()])
    treeData.value = buildTree(f.data)
    datasets.value = d.data
  } finally {
    loading.value = false
  }
}

async function prompt(title: string, value = ''): Promise<string | null> {
  try {
    const { value: v } = await ElMessageBox.prompt('请输入名称', title, { inputValue: value })
    return (v ?? '').trim() || null
  } catch {
    return null
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
  if (selected.value?.id === node.id) selected.value = null
  ElMessage.success('已删除')
  await load()
}

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
    /* 后端拒绝成环 */
  }
  await load()
}

function selectNode(node: TreeNode) {
  selected.value = node
}

async function mountDataset() {
  if (!selected.value || !mountPick.value) return ElMessage.warning('请选择数据集')
  await updateDataset(mountPick.value, { target_folder: selected.value.id })
  mountVisible.value = false
  mountPick.value = null
  await load()
  ElMessage.success('已挂载，之后跑数文件会落到此文件夹')
}
async function unmount(d: Dataset) {
  await updateDataset(d.id, { target_folder: null })
  await load()
  ElMessage.success('已取消挂载')
}

async function toggleRequestable(node: TreeNode, value: boolean) {
  await updateFolder(node.id, { requestable: value })
  node.requestable = value
  ElMessage.success(value ? '已开放申请：无权限用户可见名并申请' : '已关闭申请')
}

onMounted(load)
</script>

<template>
  <PageContainer title="目录管理" subtitle="维护文件夹目录树（拖拽移动），并把数据集挂到对应文件夹">
    <template #actions>
      <el-button :icon="FolderAdd" @click="addRoot">新建根文件夹</el-button>
    </template>

    <div class="catalog">
      <!-- 左：文件夹树 -->
      <aside class="tree-pane">
        <div class="pane-head">目录树</div>
        <el-tree
          v-loading="loading"
          :data="treeData"
          node-key="id"
          draggable
          :current-node-key="selected?.id"
          highlight-current
          :expand-on-click-node="false"
          default-expand-all
          @node-drop="onDrop"
          @node-click="selectNode"
        >
          <template #default="{ data }">
            <span class="node">
              <span class="nm"
                ><el-icon class="fi"><FolderOpened /></el-icon>{{ data.name }}</span
              >
              <span class="ops">
                <el-icon title="新建子文件夹" @click.stop="addChild(data)"><Plus /></el-icon>
                <el-icon title="重命名" @click.stop="rename(data)"><EditPen /></el-icon>
                <el-icon class="dg" title="删除" @click.stop="remove(data)"><Delete /></el-icon>
              </span>
            </span>
          </template>
        </el-tree>
        <el-empty v-if="!treeData.length && !loading" description="还没有文件夹" :image-size="50" />
      </aside>

      <!-- 右：挂载的数据集 -->
      <section class="detail">
        <template v-if="selected">
          <div class="d-head">
            <span
              ><el-icon class="fi"><FolderOpened /></el-icon><strong>{{ selected.name }}</strong> ·
              挂载的数据集</span
            >
            <div class="d-head-right">
              <span class="req-switch">
                <el-switch
                  :model-value="selected.requestable"
                  size="small"
                  @update:model-value="toggleRequestable(selected, $event as boolean)"
                />
                <span class="req-label" title="开启后，无权限用户可在门户看到此目录名并发起访问申请">
                  可被申请
                </span>
              </span>
              <el-button type="primary" :icon="Plus" @click="mountVisible = true"
                >挂载数据集</el-button
              >
            </div>
          </div>
          <div class="d-body">
            <div v-for="d in mounted" :key="d.id" class="ds rise-in">
              <div class="ds-ic">
                <el-icon><Document /></el-icon>
              </div>
              <div class="ds-main">
                <div class="ds-name">{{ d.name }}</div>
                <div class="ds-meta">
                  {{ d.datasource_name }} · 命名 {{ d.file_prefix || d.name }}_{{ d.date_format }}
                </div>
              </div>
              <el-button text type="danger" @click="unmount(d)">取消挂载</el-button>
            </div>
            <div v-if="!mounted.length" class="empty">
              <el-icon :size="26"><Document /></el-icon>
              <p>这个文件夹还没有挂载数据集</p>
              <span>点“挂载数据集”，让它跑出的文件落到这里</span>
            </div>
          </div>
        </template>
        <div v-else class="hint">
          <el-icon :size="28"><FolderOpened /></el-icon>
          <p>从左侧选择一个文件夹</p>
          <span>查看并挂载数据集</span>
        </div>
      </section>
    </div>

    <el-dialog v-model="mountVisible" :title="`挂载数据集到 · ${selected?.name}`" width="460px">
      <el-select v-model="mountPick" placeholder="选择数据集" filterable style="width: 100%">
        <el-option
          v-for="d in mountable"
          :key="d.id"
          :label="d.target_folder ? `${d.name}（当前在：${d.folder_name}）` : d.name"
          :value="d.id"
        />
      </el-select>
      <p class="tip">挂载后，该数据集每次运行生成的文件会保存到此文件夹。</p>
      <template #footer>
        <el-button @click="mountVisible = false">取消</el-button>
        <el-button type="primary" @click="mountDataset">挂载</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<style scoped>
.catalog {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  min-height: 540px;
}
.tree-pane,
.detail {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.pane-head,
.d-head {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  color: var(--ink-2);
}
.d-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.d-head-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.req-switch {
  display: flex;
  align-items: center;
  gap: 7px;
}
.req-label {
  font-size: 13px;
  color: var(--ink-2);
  cursor: default;
}
.tree-pane {
  padding-bottom: 10px;
}
.tree-pane :deep(.el-tree) {
  padding: 8px;
}
.tree-pane :deep(.el-tree-node__content) {
  height: 38px;
  border-radius: var(--r-sm);
}
.tree-pane :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: var(--accent-weak);
}
.node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}
.nm {
  display: flex;
  align-items: center;
  gap: 7px;
}
.fi {
  color: var(--accent);
}
.ops {
  display: flex;
  gap: 10px;
  opacity: 0;
  transition: opacity var(--dur-fast) var(--ease-out);
}
.ops .el-icon {
  color: var(--ink-3);
  cursor: pointer;
}
.ops .el-icon:hover {
  color: var(--ink);
}
.ops .dg:hover {
  color: var(--danger);
}
.node:hover .ops {
  opacity: 1;
}
.d-body {
  flex: 1;
  overflow: auto;
  padding: 10px;
}
.ds {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--r);
  transition: background var(--dur-fast) var(--ease-out);
}
.ds:hover {
  background: var(--surface-2);
}
.ds-ic {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--accent-weak);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
}
.ds-main {
  flex: 1;
  min-width: 0;
}
.ds-name {
  font-size: 14px;
  font-weight: 550;
}
.ds-meta {
  font-size: 12.5px;
  color: var(--ink-3);
  margin-top: 2px;
}
.tip {
  margin: 12px 0 0;
  font-size: 12.5px;
  color: var(--ink-3);
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
