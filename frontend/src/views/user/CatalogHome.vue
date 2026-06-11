<script setup lang="ts">
import {
  ArrowRight,
  Clock,
  Download,
  Folder,
  FolderOpened,
  Search,
  Star,
  StarFilled,
  View,
} from '@element-plus/icons-vue'
import { computed, nextTick, onMounted, ref } from 'vue'

import {
  type PortalFile,
  type PortalFolder,
  type PreviewData,
  downloadFile,
  getFolderFiles,
  getTree,
  getUpdates,
  listFavorites,
  previewFile,
  recentDownloads,
  searchFiles,
  toggleFavorite,
} from '@/api/portal'

const loadingTree = ref(false)
const loadingFiles = ref(false)
const tree = ref<PortalFolder[]>([])
const files = ref<PortalFile[]>([])
const currentFolderId = ref<number | null>(null)
const breadcrumb = ref<string[]>([])
const keyword = ref('')
const searching = ref(false)
const sortBy = ref<'time' | 'name'>('time')
const downloadingId = ref<number | null>(null)

// ---- v0.24 收藏 / 更新 / 最近下载 ----
const favorites = ref<{ folder_id: number; name: string }[]>([])
const favSet = computed(() => new Set(favorites.value.map((f) => f.folder_id)))
const updatesCount = ref(0)
const recent = ref<{ target: string; created_at: string }[]>([])
const LAST_SEEN_KEY = 'portal_last_seen'

async function loadFavorites() {
  favorites.value = (await listFavorites()).data
}
async function onToggleFavorite(folderId: number) {
  const { data } = await toggleFavorite(folderId)
  if (data.favorited) {
    const name = findPath(tree.value, folderId)?.slice(-1)[0] ?? '文件夹'
    favorites.value.push({ folder_id: folderId, name })
  } else {
    favorites.value = favorites.value.filter((f) => f.folder_id !== folderId)
  }
}
async function loadUpdates() {
  const since = localStorage.getItem(LAST_SEEN_KEY) || undefined
  updatesCount.value = (await getUpdates(since)).data.count
}
function markSeen() {
  localStorage.setItem(LAST_SEEN_KEY, new Date().toISOString())
  updatesCount.value = 0
}
async function loadRecent() {
  recent.value = (await recentDownloads()).data
}

const sortedFiles = computed(() => {
  const arr = [...files.value]
  if (sortBy.value === 'name') arr.sort((a, b) => a.name.localeCompare(b.name))
  else arr.sort((a, b) => b.created_at.localeCompare(a.created_at))
  return arr
})

function fmtTime(s: string) {
  return s ? s.slice(0, 16).replace('T', ' ') : '-'
}
function fmtSize(n: number | null) {
  if (!n) return '—'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

function findPath(nodes: PortalFolder[], id: number, trail: string[] = []): string[] | null {
  for (const n of nodes) {
    const next = [...trail, n.name]
    if (n.id === id) return next
    const r = findPath(n.children, id, next)
    if (r) return r
  }
  return null
}

async function loadTree() {
  loadingTree.value = true
  try {
    tree.value = (await getTree()).data
  } finally {
    loadingTree.value = false
  }
}

async function onSelectFolder(node: PortalFolder) {
  if (node.id === currentFolderId.value && !searching.value) return
  searching.value = false
  keyword.value = ''
  currentFolderId.value = node.id
  breadcrumb.value = findPath(tree.value, node.id) ?? [node.name]
  loadingFiles.value = true
  files.value = []
  try {
    const data = (await getFolderFiles(node.id)).data
    await nextTick()
    files.value = data
  } finally {
    loadingFiles.value = false
  }
}

async function onSearch() {
  const q = keyword.value.trim()
  if (!q) {
    searching.value = false
    files.value = currentFolderId.value ? (await getFolderFiles(currentFolderId.value)).data : []
    return
  }
  searching.value = true
  currentFolderId.value = null
  loadingFiles.value = true
  files.value = []
  try {
    files.value = (await searchFiles(q)).data
  } finally {
    loadingFiles.value = false
  }
}

async function handleDownload(f: PortalFile) {
  downloadingId.value = f.id
  try {
    await downloadFile(f.id, f.name)
    loadRecent() // 刷新最近下载
  } finally {
    downloadingId.value = null
  }
}

// ---- v0.24 在线预览 + 选列下载 ----
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewData = ref<PreviewData | null>(null)
const previewFileRef = ref<PortalFile | null>(null)
const selectedCols = ref<string[]>([])

async function openPreview(f: PortalFile) {
  previewFileRef.value = f
  previewVisible.value = true
  previewLoading.value = true
  previewData.value = null
  try {
    const { data } = await previewFile(f.id, 50)
    previewData.value = data
    selectedCols.value = [...data.columns] // 默认全选
  } finally {
    previewLoading.value = false
  }
}
async function downloadFromPreview() {
  const f = previewFileRef.value
  if (!f) return
  const all = previewData.value?.columns ?? []
  // 全选时不传 columns（直接给原文件），否则按选中列裁剪
  const cols = selectedCols.value.length === all.length ? undefined : selectedCols.value
  await downloadFile(f.id, f.name, cols)
}

onMounted(async () => {
  await loadTree()
  // 次要数据并行加载，失败不影响主界面
  Promise.allSettled([loadFavorites(), loadUpdates(), loadRecent()])
})

// 收藏夹快捷选择：按 folder_id 选中
async function onSelectFolderById(folderId: number) {
  const name = findPath(tree.value, folderId)?.slice(-1)[0] ?? '文件夹'
  await onSelectFolder({ id: folderId, name, children: [] })
}
</script>

<template>
  <div class="page">
    <!-- 顶部：欢迎 + 搜索 -->
    <header class="hero">
      <div class="hero-text">
        <h1 class="title">数据门户</h1>
        <p class="subtitle">浏览有权限的文件夹，下载需要的数据文件</p>
      </div>
      <div class="search">
        <el-icon class="search-icon"><Search /></el-icon>
        <input
          v-model="keyword"
          class="search-input"
          placeholder="搜索文件名…"
          @keyup.enter="onSearch"
        />
        <button v-if="keyword" class="search-clear" @click="((keyword = ''), onSearch())">
          清除
        </button>
      </div>
    </header>

    <!-- 一体化文件浏览器 -->
    <div class="explorer">
      <!-- 左：文件夹树 -->
      <aside class="tree-pane">
        <div v-if="favorites.length" class="fav-zone">
          <div class="pane-head">
            <el-icon class="fav-star"><StarFilled /></el-icon> 我的收藏
          </div>
          <div class="fav-chips">
            <button
              v-for="f in favorites"
              :key="f.folder_id"
              class="fav-chip"
              :class="{ on: currentFolderId === f.folder_id }"
              @click="onSelectFolderById(f.folder_id)"
            >
              {{ f.name }}
            </button>
          </div>
        </div>
        <div class="pane-head">数据目录</div>
        <div v-if="loadingTree" class="tree-skeleton">
          <div
            v-for="i in 5"
            :key="i"
            class="skeleton sk-row"
            :style="{ width: 70 - i * 6 + '%' }"
          />
        </div>
        <el-tree
          v-else-if="tree.length"
          :data="tree"
          node-key="id"
          :props="{ label: 'name', children: 'children' }"
          :current-node-key="currentFolderId ?? undefined"
          :expand-on-click-node="false"
          default-expand-all
          highlight-current
          @node-click="onSelectFolder"
        >
          <template #default="{ node, data }">
            <span class="tnode">
              <el-icon class="tnode-icon">
                <FolderOpened v-if="node.expanded && data.children.length" />
                <Folder v-else />
              </el-icon>
              <span class="tnode-label">{{ data.name }}</span>
              <button
                class="tnode-star"
                :class="{ on: favSet.has(data.id) }"
                :title="favSet.has(data.id) ? '取消收藏' : '收藏'"
                @click.stop="onToggleFavorite(data.id)"
              >
                <el-icon><StarFilled v-if="favSet.has(data.id)" /><Star v-else /></el-icon>
              </button>
            </span>
          </template>
        </el-tree>
        <div v-else class="pane-empty">
          <el-icon :size="26"><Folder /></el-icon>
          <p>还没有授权给你的目录</p>
          <span>请联系管理员开通</span>
        </div>

        <div v-if="recent.length" class="recent-zone">
          <div class="pane-head"><el-icon><Clock /></el-icon> 最近下载</div>
          <ul class="recent-list">
            <li v-for="(r, i) in recent.slice(0, 5)" :key="i" :title="r.target">
              <el-icon class="rz-ic"><Download /></el-icon>
              <span class="rz-name">{{ r.target }}</span>
            </li>
          </ul>
        </div>
      </aside>

      <!-- 右：文件列表 -->
      <section class="file-pane">
        <div class="file-head">
          <nav class="crumb">
            <template v-if="searching">
              <el-icon><Search /></el-icon>
              <span class="crumb-seg active">搜索：“{{ keyword }}”</span>
            </template>
            <template v-else-if="breadcrumb.length">
              <el-icon><FolderOpened /></el-icon>
              <template v-for="(c, i) in breadcrumb" :key="i">
                <span class="crumb-seg" :class="{ active: i === breadcrumb.length - 1 }">{{
                  c
                }}</span>
                <el-icon v-if="i < breadcrumb.length - 1" class="crumb-sep"><ArrowRight /></el-icon>
              </template>
            </template>
            <span v-else class="crumb-hint">从左侧选择一个文件夹</span>
          </nav>
          <div class="file-tools">
            <button v-if="updatesCount" class="updates-pill" title="标记为已读" @click="markSeen">
              <span class="dot-live" /> {{ updatesCount }} 个新文件
            </button>
            <span v-if="sortedFiles.length" class="file-count"
              >{{ sortedFiles.length }} 个文件</span
            >
            <div class="seg">
              <button :class="{ on: sortBy === 'time' }" @click="sortBy = 'time'">时间</button>
              <button :class="{ on: sortBy === 'name' }" @click="sortBy = 'name'">名称</button>
            </div>
          </div>
        </div>

        <div class="file-body">
          <!-- 加载骨架 -->
          <div v-if="loadingFiles" class="file-list">
            <div v-for="i in 6" :key="i" class="file-row sk">
              <div class="skeleton sk-ic" />
              <div class="sk-lines">
                <div class="skeleton sk-l1" />
                <div class="skeleton sk-l2" />
              </div>
            </div>
          </div>

          <!-- 文件列表 -->
          <div v-else-if="sortedFiles.length" class="file-list">
            <div
              v-for="(f, i) in sortedFiles"
              :key="f.id"
              class="file-row rise-in"
              :style="{ animationDelay: Math.min(i * 28, 280) + 'ms' }"
              @click="handleDownload(f)"
            >
              <div class="file-ic">XLS</div>
              <div class="file-main">
                <div class="file-name">{{ f.name }}</div>
                <div class="file-meta">
                  <span v-if="f.row_count != null">{{ f.row_count }} 行</span>
                  <span class="dot" />
                  <span>{{ fmtSize(f.file_size) }}</span>
                  <span class="dot" />
                  <span>{{ fmtTime(f.created_at) }}</span>
                </div>
              </div>
              <button class="dl-btn ghost" @click.stop="openPreview(f)">
                <el-icon><View /></el-icon>
                <span>预览</span>
              </button>
              <button
                class="dl-btn"
                :class="{ busy: downloadingId === f.id }"
                @click.stop="handleDownload(f)"
              >
                <el-icon :class="{ 'dl-spin': downloadingId === f.id }"><Download /></el-icon>
                <span>下载</span>
              </button>
            </div>
          </div>

          <!-- 空状态（教学型）-->
          <div v-else class="file-empty">
            <div class="empty-art">
              <el-icon :size="30"><component :is="searching ? Search : FolderOpened" /></el-icon>
            </div>
            <p class="empty-title">
              {{
                searching
                  ? '没有匹配的文件'
                  : currentFolderId
                    ? '这个文件夹还没有文件'
                    : '选择左侧的文件夹开始'
              }}
            </p>
            <span class="empty-sub">
              {{
                searching
                  ? '换个关键词试试'
                  : currentFolderId
                    ? '管理员跑数后，文件会自动出现在这里'
                    : '你有权限的目录都在左侧'
              }}
            </span>
          </div>
        </div>
      </section>
    </div>

    <!-- v0.24 在线预览 + 选列下载 -->
    <el-dialog v-model="previewVisible" :title="previewFileRef?.name || '预览'" width="80%" top="6vh">
      <div v-loading="previewLoading">
        <div v-if="previewData" class="pv-tools">
          <span class="pv-hint">预览前 50 行 · 选择要下载的列：</span>
          <el-select
            v-model="selectedCols"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="选择列"
            class="pv-select"
          >
            <el-option v-for="c in previewData.columns" :key="c" :label="c" :value="c" />
          </el-select>
          <el-button type="primary" :icon="Download" @click="downloadFromPreview">
            下载{{
              selectedCols.length && selectedCols.length !== previewData.columns.length
                ? `选中 ${selectedCols.length} 列`
                : '全部'
            }}
          </el-button>
        </div>
        <el-table
          v-if="previewData"
          :data="previewData.rows"
          border
          height="460"
          size="small"
        >
          <el-table-column
            v-for="(col, i) in previewData.columns"
            :key="i"
            :label="col"
            min-width="120"
          >
            <template #default="{ row }">{{ row[i] }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

/* —— Hero —— */
.hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}
.title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.subtitle {
  margin: 6px 0 0;
  color: var(--ink-2);
  font-size: 14px;
}
.search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 340px;
  max-width: 100%;
  height: 42px;
  padding: 0 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-full);
  box-shadow: var(--shadow-sm);
  transition:
    border-color var(--dur) var(--ease-out),
    box-shadow var(--dur) var(--ease-out);
}
.search:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-weak);
}
.search-icon {
  color: var(--ink-3);
}
.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--ink);
}
.search-clear {
  border: none;
  background: transparent;
  color: var(--ink-3);
  font-size: 13px;
  cursor: pointer;
  padding: 2px 4px;
}
.search-clear:hover {
  color: var(--ink);
}

/* —— Explorer 一体化容器 —— */
.explorer {
  display: grid;
  grid-template-columns: 288px 1fr;
  height: calc(100vh - 212px);
  min-height: 560px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow);
  overflow: hidden;
}

/* 左：树 */
.tree-pane {
  background: var(--surface-2);
  border-right: 1px solid var(--border);
  padding: 14px 12px;
  overflow: auto;
}
.pane-head {
  font-size: 12px;
  font-weight: 650;
  letter-spacing: 0.02em;
  color: var(--ink-3);
  text-transform: uppercase;
  padding: 4px 8px 12px;
}
.tnode {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.tnode-icon {
  color: var(--accent);
  flex-shrink: 0;
}
.tnode-label {
  flex: 1;
  font-size: 14px;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tnode-star {
  display: flex;
  align-items: center;
  border: none;
  background: transparent;
  color: var(--ink-3);
  cursor: pointer;
  padding: 2px;
  opacity: 0;
  transition:
    opacity var(--dur-fast) var(--ease-out),
    color var(--dur-fast) var(--ease-out);
}
.tree-pane :deep(.el-tree-node__content:hover) .tnode-star,
.tnode-star.on {
  opacity: 1;
}
.tnode-star.on {
  color: #f0a020;
}
.tnode-star:hover {
  color: #f0a020;
}
/* 收藏快捷区 */
.fav-zone {
  margin-bottom: 6px;
}
.fav-star {
  color: #f0a020;
  vertical-align: -2px;
}
.fav-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 4px 12px;
}
.fav-chip {
  max-width: 100%;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--ink-2);
  font-size: 12.5px;
  padding: 4px 10px;
  border-radius: var(--r-full);
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: all var(--dur-fast) var(--ease-out);
}
.fav-chip:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.fav-chip.on {
  background: var(--accent-weak);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}
/* 最近下载 */
.recent-zone {
  margin-top: 14px;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}
.recent-list {
  list-style: none;
  margin: 0;
  padding: 0 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.recent-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--r-sm);
  font-size: 13px;
  color: var(--ink-2);
}
.rz-ic {
  color: var(--ink-3);
  flex-shrink: 0;
}
.rz-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* 更新提示 */
.updates-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--accent);
  background: var(--accent-weak);
  color: var(--accent);
  font-size: 12.5px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--r-full);
  cursor: pointer;
}
.dot-live {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}
@media (prefers-reduced-motion: reduce) {
  .dot-live {
    animation: none;
  }
}
.pane-empty {
  text-align: center;
  color: var(--ink-3);
  padding: 48px 12px;
}
.pane-empty p {
  margin: 12px 0 2px;
  color: var(--ink-2);
  font-size: 14px;
}
.pane-empty span {
  font-size: 12px;
}
.tree-skeleton {
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.sk-row {
  height: 16px;
}

/* el-tree 贴合设计：节点高度/圆角/hover/选中 */
.tree-pane :deep(.el-tree) {
  background: transparent;
}
.tree-pane :deep(.el-tree-node__content) {
  height: 38px;
  border-radius: var(--r-sm);
  margin: 1px 0;
  transition: background var(--dur-fast) var(--ease-out);
}
.tree-pane :deep(.el-tree-node__content:hover) {
  background: var(--surface);
}
.tree-pane :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: var(--accent-weak);
}
.tree-pane :deep(.el-tree-node.is-current > .el-tree-node__content) .tnode-label {
  color: var(--accent);
  font-weight: 600;
}
.tree-pane :deep(.el-tree-node.is-current > .el-tree-node__content) .tnode-icon {
  color: var(--accent);
}

/* 右：文件 */
.file-pane {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.file-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.crumb {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ink-2);
  min-width: 0;
  overflow: hidden;
}
.crumb-seg {
  font-size: 14px;
  white-space: nowrap;
}
.crumb-seg.active {
  color: var(--ink);
  font-weight: 600;
}
.crumb-sep {
  color: var(--ink-3);
  font-size: 12px;
}
.crumb-hint {
  color: var(--ink-3);
  font-size: 14px;
}
.file-tools {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}
.file-count {
  font-size: 13px;
  color: var(--ink-3);
}
.seg {
  display: inline-flex;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  padding: 2px;
}
.seg button {
  border: none;
  background: transparent;
  padding: 5px 12px;
  font-size: 13px;
  color: var(--ink-2);
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.seg button.on {
  background: var(--surface);
  color: var(--ink);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.file-body {
  flex: 1;
  padding: 10px;
  overflow: auto;
}
.file-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.file-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  border-radius: var(--r);
  cursor: pointer;
  transition:
    background var(--dur-fast) var(--ease-out),
    transform var(--dur-fast) var(--ease-out);
}
.file-row:hover {
  background: var(--surface-2);
}
.file-row:active {
  transform: translateY(1px);
}
.file-ic {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--success) 12%, white);
  color: var(--success);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.file-main {
  flex: 1;
  min-width: 0;
}
.file-name {
  font-size: 14px;
  font-weight: 550;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 3px;
  font-size: 12.5px;
  color: var(--ink-3);
}
.dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--border-strong);
}
.dl-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--border-strong);
  background: var(--surface);
  color: var(--ink-2);
  font-size: 13px;
  font-weight: 550;
  padding: 7px 14px;
  border-radius: var(--r-sm);
  cursor: pointer;
  opacity: 0;
  transform: translateX(4px);
  transition: all var(--dur-fast) var(--ease-out);
}
.file-row:hover .dl-btn {
  opacity: 1;
  transform: translateX(0);
}
.dl-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-weak);
}
.dl-btn.busy {
  opacity: 1;
}
.dl-btn.ghost {
  margin-right: 8px;
}
.pv-tools {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.pv-hint {
  font-size: 13px;
  color: var(--ink-3);
}
.pv-select {
  min-width: 260px;
}
.dl-spin {
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 文件骨架 */
.file-row.sk {
  cursor: default;
}
.sk-ic {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  flex-shrink: 0;
}
.sk-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sk-l1 {
  height: 13px;
  width: 46%;
}
.sk-l2 {
  height: 11px;
  width: 28%;
}

/* 空状态 */
.file-empty {
  height: 100%;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
}
.empty-art {
  width: 68px;
  height: 68px;
  border-radius: 18px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--ink-3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.empty-title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}
.empty-sub {
  font-size: 13px;
  color: var(--ink-3);
  max-width: 320px;
}

@media (max-width: 820px) {
  .explorer {
    grid-template-columns: 1fr;
  }
  .tree-pane {
    border-right: none;
    border-bottom: 1px solid var(--border);
    max-height: 220px;
  }
}
</style>
