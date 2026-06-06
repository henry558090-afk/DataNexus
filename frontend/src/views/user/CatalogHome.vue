<script setup lang="ts">
import { Document, Folder, Search } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { type PortalDepartment, getTree } from '@/api/portal'

const router = useRouter()

const loading = ref(false)
const tree = ref<PortalDepartment[]>([])
const keyword = ref('')
const selected = ref<{ type: 'dept' | 'cat'; id: number } | null>(null)

interface FlatItem {
  id: number
  name: string
  description: string
  deptId: number
  deptName: string
  catId: number
  catName: string
}

// 扁平化所有可见数据集，便于搜索与筛选
const allItems = computed<FlatItem[]>(() => {
  const items: FlatItem[] = []
  for (const dep of tree.value) {
    for (const cat of dep.categories) {
      for (const ds of cat.datasets) {
        items.push({
          id: ds.id,
          name: ds.name,
          description: ds.description,
          deptId: dep.id,
          deptName: dep.name,
          catId: cat.id,
          catName: cat.name,
        })
      }
    }
  }
  return items
})

// 左侧树数据
const treeData = computed(() =>
  tree.value.map((dep) => ({
    key: `dept-${dep.id}`,
    name: dep.name,
    type: 'dept' as const,
    id: dep.id,
    children: dep.categories.map((cat) => ({
      key: `cat-${cat.id}`,
      name: cat.name,
      type: 'cat' as const,
      id: cat.id,
    })),
  })),
)

// 主区显示的数据集
const displayed = computed<FlatItem[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (kw) return allItems.value.filter((i) => i.name.toLowerCase().includes(kw))
  if (!selected.value) return allItems.value
  if (selected.value.type === 'dept') {
    return allItems.value.filter((i) => i.deptId === selected.value!.id)
  }
  return allItems.value.filter((i) => i.catId === selected.value!.id)
})

const heading = computed(() => {
  if (keyword.value.trim()) return `搜索 “${keyword.value.trim()}”`
  if (!selected.value) return '全部数据'
  const item = allItems.value.find((i) =>
    selected.value!.type === 'cat'
      ? i.catId === selected.value!.id
      : i.deptId === selected.value!.id,
  )
  if (!item) return '全部数据'
  return selected.value.type === 'cat' ? `${item.deptName} / ${item.catName}` : item.deptName
})

function onNodeClick(node: { type: 'dept' | 'cat'; id: number }) {
  keyword.value = ''
  selected.value = { type: node.type, id: node.id }
}

async function load() {
  loading.value = true
  try {
    tree.value = (await getTree()).data
  } finally {
    loading.value = false
  }
}

function open(id: number) {
  router.push(`/dataset/${id}`)
}

onMounted(load)
</script>

<template>
  <div v-loading="loading" class="portal">
    <aside class="side">
      <div class="side-title">数据目录</div>
      <el-tree
        :data="treeData"
        node-key="key"
        :props="{ label: 'name', children: 'children' }"
        :expand-on-click-node="false"
        default-expand-all
        @node-click="onNodeClick"
      >
        <template #default="{ data }">
          <span class="node">
            <el-icon><component :is="data.type === 'dept' ? Folder : Document" /></el-icon>
            {{ data.name }}
          </span>
        </template>
      </el-tree>
      <el-empty v-if="!tree.length && !loading" description="暂无授权数据" :image-size="50" />
    </aside>

    <main class="main">
      <div class="bar">
        <h2 class="h">{{ heading }}</h2>
        <el-input
          v-model="keyword"
          class="search"
          :prefix-icon="Search"
          placeholder="搜索数据文件…"
          clearable
        />
      </div>

      <div v-if="displayed.length" class="cards">
        <el-card
          v-for="item in displayed"
          :key="item.id"
          class="ds-card"
          shadow="hover"
          @click="open(item.id)"
        >
          <div class="ds-inner">
            <el-icon class="ds-icon"><Document /></el-icon>
            <div class="ds-body">
              <div class="ds-name">{{ item.name }}</div>
              <div class="ds-path">{{ item.deptName }} / {{ item.catName }}</div>
            </div>
          </div>
        </el-card>
      </div>
      <el-empty v-else description="没有匹配的数据" />
    </main>
  </div>
</template>

<style scoped>
.portal {
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
.node {
  display: flex;
  align-items: center;
  gap: 6px;
}
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 16px;
}
.h {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}
.search {
  max-width: 320px;
}
.search :deep(.el-input__wrapper) {
  border-radius: 999px;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}
.ds-card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  cursor: pointer;
}
.ds-inner {
  display: flex;
  align-items: center;
  gap: 14px;
}
.ds-icon {
  font-size: 24px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  padding: 10px;
  border-radius: 12px;
}
.ds-name {
  font-weight: 600;
}
.ds-path {
  font-size: 12px;
  color: var(--app-text-secondary);
  margin-top: 2px;
}
</style>
