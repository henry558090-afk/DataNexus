<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { ref } from 'vue'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const keyword = ref('')
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

    <section class="block">
      <h3 class="block-title">按部门浏览</h3>
      <el-empty description="数据目录将在 v0.10 开放（部门 → 分类 → 数据文件）" />
    </section>
  </div>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 32px 0 28px;
}
.title {
  margin: 0 0 8px;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.5px;
}
.sub {
  margin: 0 0 24px;
  color: var(--app-text-secondary);
  font-size: 15px;
}
.search {
  max-width: 560px;
}
.search :deep(.el-input__wrapper) {
  border-radius: 999px;
  padding: 4px 18px;
  box-shadow: 0 6px 20px rgba(79, 110, 247, 0.12);
}
.block {
  margin-top: 16px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 24px;
}
.block-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 700;
}
</style>
