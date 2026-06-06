<script setup lang="ts">
import { Lock, User } from '@element-plus/icons-vue'
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
    // 按角色分流：管理员进管理端，普通用户进数据门户
    router.push({ path: auth.isManager ? '/admin' : '/' })
  } catch {
    // 错误提示已由 http 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login">
    <div class="card">
      <div class="brand">
        <div class="brand-mark">DN</div>
        <div class="brand-text">
          <h1 class="brand-name">data-nexus</h1>
          <p class="brand-sub">数据共享平台</p>
        </div>
      </div>

      <h2 class="welcome">欢迎回来 👋</h2>
      <p class="tip">登录以继续使用数据共享平台</p>

      <el-form label-position="top" class="form" @submit.prevent="handleLogin">
        <el-form-item label="账号">
          <el-input
            v-model="form.username"
            size="large"
            :prefix-icon="User"
            placeholder="请输入账号"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            size="large"
            show-password
            :prefix-icon="Lock"
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="submit"
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>
    </div>

    <p class="footer">© 2026 data-nexus · 内部数据共享平台</p>
  </div>
</template>

<style scoped>
.login {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background:
    radial-gradient(1200px 600px at 15% 10%, #e8edff 0%, transparent 55%),
    radial-gradient(1000px 600px at 90% 90%, #eaf0ff 0%, transparent 50%),
    linear-gradient(135deg, #f6f8ff 0%, #f2f5fd 100%);
}
.card {
  width: 400px;
  background: #fff;
  border-radius: 18px;
  padding: 40px 36px;
  box-shadow: 0 12px 40px rgba(79, 110, 247, 0.12);
  border: 1px solid #eef1fb;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
}
.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #4f6ef7, #7c8cff);
  color: #fff;
  font-weight: 700;
  font-size: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(79, 110, 247, 0.35);
}
.brand-name {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}
.brand-sub {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--app-text-secondary);
}
.welcome {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
}
.tip {
  margin: 0 0 24px;
  font-size: 14px;
  color: var(--app-text-secondary);
}
.submit {
  width: 100%;
  margin-top: 8px;
  font-weight: 600;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #4f6ef7, #6b80ff);
  border: none;
}
.footer {
  font-size: 12px;
  color: #a8b0c0;
}
</style>
