<script setup lang="ts">
import PageContainer from '@/components/PageContainer.vue'
</script>

<template>
  <PageContainer title="查询任务" subtitle="编写 SQL，运行并导出 Excel">
    <el-card class="placeholder" shadow="never">
      <el-empty description="查询任务（SQL→Excel）将在 v0.06+ 实现" />
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
