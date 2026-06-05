<script setup lang="ts">
import PageContainer from '@/components/PageContainer.vue'
</script>

<template>
  <PageContainer title="目录管理" subtitle="维护部门与分类（部门 → 分类）">
    <el-card class="ph" shadow="never">
      <el-empty description="部门 / 分类管理将在 v0.10 实现" />
    </el-card>
  </PageContainer>
</template>

<style scoped>
.ph {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 24px 0;
}
</style>
