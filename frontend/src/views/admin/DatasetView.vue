<script setup lang="ts">
import PageContainer from '@/components/PageContainer.vue'
</script>

<template>
  <PageContainer title="数据集" subtitle="编写 SQL，运行并导出 Excel">
    <el-card class="ph" shadow="never">
      <el-empty description="数据集编辑器 + SQL→Excel 将在 v0.09 实现" />
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
