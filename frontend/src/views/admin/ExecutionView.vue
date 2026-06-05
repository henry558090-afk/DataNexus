<script setup lang="ts">
import PageContainer from '@/components/PageContainer.vue'
</script>

<template>
  <PageContainer title="执行记录" subtitle="数据集运行历史与生成的文件">
    <el-card class="ph" shadow="never">
      <el-empty description="执行记录与审计将在 v0.09+ 实现" />
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
