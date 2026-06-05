<script setup lang="ts">
import PageContainer from '@/components/PageContainer.vue'
</script>

<template>
  <PageContainer title="执行记录" subtitle="查看历史执行与下载结果文件">
    <el-card class="placeholder" shadow="never">
      <el-empty description="执行记录与下载将在 v0.06+ 实现" />
    </el-card>
  </PageContainer>
</template>

<style scoped>
.placeholder {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 24px 0;
}
</style>
