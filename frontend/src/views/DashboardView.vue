<script setup lang="ts">
import { onMounted, ref } from 'vue'

import http from '@/api/http'

const me = ref<{ username: string; is_staff: boolean } | null>(null)

onMounted(async () => {
  // 拉取当前用户，验证前后端 Token 认证链路打通
  const { data } = await http.get('/auth/me/')
  me.value = data
})
</script>

<template>
  <div>
    <h2>概览</h2>
    <el-alert
      type="success"
      :closable="false"
      title="前后端已打通"
      description="登录态正常，下一步将接入数据源与查询任务。"
    />
    <el-descriptions class="info" :column="1" border>
      <el-descriptions-item label="当前用户">
        {{ me?.username ?? '加载中...' }}
      </el-descriptions-item>
      <el-descriptions-item label="管理员">
        {{ me ? (me.is_staff ? '是' : '否') : '加载中...' }}
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<style scoped>
.info {
  margin-top: 16px;
  max-width: 480px;
}
</style>
