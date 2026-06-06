<script setup lang="ts">
import { Document, Search } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { type PortalDepartment, getTree } from '@/api/portal'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const tree = ref<PortalDepartment[]>([])
const keyword = ref('')

// 简单的前端搜索：按数据集名过滤，裁掉空分支
const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return tree.value
  return tree.value
    .map((dep) => ({
      ...dep,
      categories: dep.categories
        .map((cat) => ({
          ...cat,
          datasets: cat.datasets.filter((d) => d.name.toLowerCase().includes(kw)),
        }))
        .filter((cat) => cat.datasets.length),
    }))
    .filter((dep) => dep.categories.length)
})

const isEmpty = computed(() => !loading.value && filtered.value.length === 0)

async function load() {
  loading.value = true
  try {
    tree.value = (await getTree()).data
  } finally {
    loading.value = false
  }
}

function openDataset(id: number) {
  router.push(`/dataset/${id}`)
}

onMounted(load)
</script>

<template>
  <div>
    <section class="hero">
      <h1 class="title">你好，{{ auth.username || '访客' }}</h1>
      <p class="sub">在数据门户中找到你需要的数据文件，一键下载使用。</p>
      <el-input
        v-model="keyword"
        size="large"
        class="search"
        :prefix-icon="Search"
        placeholder="搜索数据文件…"
      />
    </section>

    <div v-loading="loading">
      <section v-for="dep in filtered" :key="dep.id" class="dept">
        <h3 class="dept-name">{{ dep.name }}</h3>
        <div v-for="cat in dep.categories" :key="cat.id" class="cat">
          <div class="cat-name">{{ cat.name }}</div>
          <div class="cards">
            <el-card
              v-for="ds in cat.datasets"
              :key="ds.id"
              class="ds-card"
              shadow="hover"
              @click="openDataset(ds.id)"
            >
              <div class="ds-inner">
                <el-icon class="ds-icon"><Document /></el-icon>
                <div>
                  <div class="ds-name">{{ ds.name }}</div>
                  <div class="ds-desc">{{ ds.description || '点击查看与下载' }}</div>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </section>

      <el-empty v-if="isEmpty" description="暂无可见的数据，请联系管理员分配权限" />
    </div>
  </div>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 24px 0 20px;
}
.title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 800;
}
.sub {
  margin: 0 0 20px;
  color: var(--app-text-secondary);
}
.search {
  max-width: 560px;
}
.search :deep(.el-input__wrapper) {
  border-radius: 999px;
  padding: 4px 18px;
  box-shadow: 0 6px 20px rgba(79, 110, 247, 0.12);
}
.dept {
  margin-top: 24px;
}
.dept-name {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 700;
}
.cat {
  margin-bottom: 16px;
}
.cat-name {
  font-size: 13px;
  color: var(--app-text-secondary);
  margin-bottom: 8px;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
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
  font-size: 26px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  padding: 10px;
  border-radius: 12px;
}
.ds-name {
  font-weight: 600;
}
.ds-desc {
  font-size: 12px;
  color: var(--app-text-secondary);
  margin-top: 2px;
}
</style>
