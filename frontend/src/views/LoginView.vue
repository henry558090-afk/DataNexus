<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function handleLogin(): Promise<void> {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push({ path: '/' })
  } catch {
    // 错误提示已由 http 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login">
    <el-card class="card">
      <h2 class="title">data-nexus 数据共享平台</h2>
      <el-form label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="账号">
          <el-input v-model="form.username" placeholder="请输入账号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button type="primary" class="submit" :loading="loading" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.card {
  width: 360px;
}
.title {
  text-align: center;
  margin: 0 0 20px;
  font-size: 18px;
}
.submit {
  width: 100%;
}
</style>
