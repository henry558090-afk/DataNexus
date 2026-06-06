<script setup lang="ts">
import { Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

import {
  type Department,
  createCategory,
  createDepartment,
  deleteCategory,
  deleteDepartment,
  listDepartments,
} from '@/api/catalog'
import PageContainer from '@/components/PageContainer.vue'

const loading = ref(false)
const departments = ref<Department[]>([])
const activeDeptId = ref<number | null>(null)
const newDept = ref('')
const newCat = ref('')

const activeDept = computed(
  () => departments.value.find((d) => d.id === activeDeptId.value) ?? null,
)

async function load() {
  loading.value = true
  try {
    departments.value = (await listDepartments()).data
    if (!activeDeptId.value && departments.value.length) {
      activeDeptId.value = departments.value[0].id
    }
  } finally {
    loading.value = false
  }
}

async function addDept() {
  if (!newDept.value.trim()) return
  const { data } = await createDepartment(newDept.value.trim())
  newDept.value = ''
  ElMessage.success('已添加部门')
  await load()
  activeDeptId.value = data.id
}

async function removeDept(id: number) {
  await ElMessageBox.confirm('删除部门会一并删除其下分类，确认？', '提示', { type: 'warning' })
  await deleteDepartment(id)
  if (activeDeptId.value === id) activeDeptId.value = null
  ElMessage.success('已删除')
  await load()
}

async function addCat() {
  if (!newCat.value.trim() || !activeDeptId.value) return
  await createCategory(newCat.value.trim(), activeDeptId.value)
  newCat.value = ''
  ElMessage.success('已添加分类')
  await load()
}

async function removeCat(id: number) {
  await ElMessageBox.confirm('确认删除该分类？', '提示', { type: 'warning' })
  await deleteCategory(id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <PageContainer title="目录管理" subtitle="维护部门与分类（部门 → 分类）">
    <el-row v-loading="loading" :gutter="16">
      <el-col :span="10">
        <el-card class="card" shadow="never">
          <template #header>
            <div class="head">
              <span>部门</span>
              <div class="add">
                <el-input
                  v-model="newDept"
                  size="small"
                  placeholder="新部门名"
                  @keyup.enter="addDept"
                />
                <el-button size="small" type="primary" :icon="Plus" @click="addDept" />
              </div>
            </div>
          </template>
          <div
            v-for="d in departments"
            :key="d.id"
            class="item"
            :class="{ active: d.id === activeDeptId }"
            @click="activeDeptId = d.id"
          >
            <span>{{ d.name }}</span>
            <el-button text type="danger" :icon="Delete" @click.stop="removeDept(d.id)" />
          </div>
          <el-empty v-if="!departments.length" description="还没有部门" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card class="card" shadow="never">
          <template #header>
            <div class="head">
              <span>分类{{ activeDept ? ` · ${activeDept.name}` : '' }}</span>
              <div v-if="activeDept" class="add">
                <el-input
                  v-model="newCat"
                  size="small"
                  placeholder="新分类名"
                  @keyup.enter="addCat"
                />
                <el-button size="small" type="primary" :icon="Plus" @click="addCat" />
              </div>
            </div>
          </template>
          <template v-if="activeDept">
            <div v-for="c in activeDept.categories" :key="c.id" class="item">
              <span>{{ c.name }}</span>
              <el-button text type="danger" :icon="Delete" @click="removeCat(c.id)" />
            </div>
            <el-empty
              v-if="!activeDept.categories.length"
              description="该部门还没有分类"
              :image-size="60"
            />
          </template>
          <el-empty v-else description="先选择左侧部门" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </PageContainer>
</template>

<style scoped>
.card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  min-height: 360px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.add {
  display: flex;
  gap: 8px;
  width: 200px;
}
.item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
}
.item:hover {
  background: #f3f5fb;
}
.item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}
</style>
