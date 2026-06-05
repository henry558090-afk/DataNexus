<script setup lang="ts">
import PageContainer from '@/components/PageContainer.vue'
</script>

<template>
  <PageContainer title="数据源" subtitle="管理 Oracle 数据源连接（只读）">
    <el-card class="ph" shadow="never">
      <el-empty description="数据源 CRUD + 测试连接将在 v0.08 实现" />
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
