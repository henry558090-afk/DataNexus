<script setup lang="ts">
import { Document, Download, Folder as FolderIcon, Search } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'

import {
  type PortalFile,
  type PortalFolder,
  downloadFile,
  getFolderFiles,
  getTree,
  searchFiles,
} from '@/api/portal'

const loadingTree = ref(false)
const loadingFiles = ref(false)
const tree = ref<PortalFolder[]>([])
const files = ref<PortalFile[]>([])
const currentFolder = ref<PortalFolder | null>(null)
const breadcrumb = ref<string[]>([])
const keyword = ref('')
const searching = ref(false)
const sortBy = ref<'time' | 'name'>('time')

const sortedFiles = computed(() => {
  const arr = [...files.value]
  if (sortBy.value === 'name') arr.sort((a, b) => a.name.localeCompare(b.name))
  else arr.sort((a, b) => b.created_at.localeCompare(a.created_at))
  return arr
})

function fmtTime(s: string) {
  return s ? s.slice(0, 19).replace('T', ' ') : '-'
}
function fmtSize(n: number | null) {
  if (!n) return '-'
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
  searching.value = false
  keyword.value = ''
  currentFolder.value = node
  breadcrumb.value = findPath(tree.value, node.id) ?? [node.name]
  loadingFiles.value = true
  try {
    files.value = (await getFolderFiles(node.id)).data
  } finally {
    loadingFiles.value = false
  }
}

async function onSearch() {
  const q = keyword.value.trim()
  if (!q) {
    searching.value = false
    return
  }
  searching.value = true
  currentFolder.value = null
  loadingFiles.value = true
  try {
    files.value = (await searchFiles(q)).data
  } finally {
    loadingFiles.value = false
  }
}

async function handleDownload(f: PortalFile) {
  await downloadFile(f.id, f.name)
}

onMounted(loadTree)
</script>

<template>
  <div>
    <div class="searchbar">
      <el-input
        v-model="keyword"
        size="large"
        class="search"
        :prefix-icon="Search"
        placeholder="搜索全部数据文件…"
        clearable
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-button size="large" type="primary" @click="onSearch">搜索</el-button>
    </div>

    <div class="explorer">
      <aside class="side">
        <div class="side-title">数据目录</div>
        <el-tree
          v-loading="loadingTree"
          :data="tree"
          node-key="id"
          :props="{ label: 'name', children: 'children' }"
          :expand-on-click-node="false"
          default-expand-all
          @node-click="onSelectFolder"
        >
          <template #default="{ data }">
            <span class="tnode"
              ><el-icon><FolderIcon /></el-icon>{{ data.name }}</span
            >
          </template>
        </el-tree>
        <el-empty v-if="!tree.length && !loadingTree" description="暂无授权目录" :image-size="50" />
      </aside>

      <main class="main">
        <div class="bar">
          <div class="crumb">
            <template v-if="searching">搜索结果：“{{ keyword }}”</template>
            <template v-else-if="breadcrumb.length">
              <el-icon><FolderIcon /></el-icon>
              <span v-for="(c, i) in breadcrumb" :key="i" class="cseg">
                {{ c }}<span v-if="i < breadcrumb.length - 1"> / </span>
              </span>
            </template>
            <span v-else class="muted">← 从左侧选择文件夹</span>
          </div>
          <el-radio-group v-model="sortBy" size="small">
            <el-radio-button value="time">按时间</el-radio-button>
            <el-radio-button value="name">按名称</el-radio-button>
          </el-radio-group>
        </div>

        <el-table v-loading="loadingFiles" :data="sortedFiles">
          <el-table-column label="文件名" min-width="240">
            <template #default="{ row }">
              <span class="fname"
                ><el-icon class="fic"><Document /></el-icon>{{ row.name }}</span
              >
            </template>
          </el-table-column>
          <el-table-column prop="row_count" label="行数" width="100" />
          <el-table-column label="大小" width="110">
            <template #default="{ row }">{{ fmtSize(row.file_size) }}</template>
          </el-table-column>
          <el-table-column label="时间" min-width="170">
            <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" :icon="Download" @click="handleDownload(row)">
                下载
              </el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="searching ? '没有匹配的文件' : '该文件夹暂无文件'" />
          </template>
        </el-table>
      </main>
    </div>
  </div>
</template>

<style scoped>
.searchbar {
  display: flex;
  gap: 12px;
  max-width: 720px;
  margin: 8px auto 24px;
}
.search :deep(.el-input__wrapper) {
  border-radius: 999px;
  box-shadow: 0 6px 20px rgba(79, 110, 247, 0.12);
}
.explorer {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
  align-items: start;
}
.side {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 16px;
  position: sticky;
  top: 88px;
}
.side-title {
  font-weight: 700;
  margin-bottom: 12px;
}
.tnode {
  display: flex;
  align-items: center;
  gap: 6px;
}
.main {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 16px 20px;
}
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.crumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}
.fname {
  display: flex;
  align-items: center;
  gap: 8px;
}
.fic {
  color: var(--el-color-primary);
}
.muted {
  color: var(--app-text-secondary);
  font-weight: 400;
}
</style>
