<script setup lang="ts">
import PageContainer from '@/components/PageContainer.vue'
</script>

<template>
  <PageContainer title="用户与权限" subtitle="角色分配（老板/总监/主管/成员）与授权">
    <el-card class="ph" shadow="never">
      <el-empty description="用户管理 + 角色授权将在 v0.11 实现" />
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
