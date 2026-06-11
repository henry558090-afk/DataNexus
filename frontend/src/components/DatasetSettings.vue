<script setup lang="ts">
import { Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref, watch } from 'vue'

import {
  type Dataset,
  type MaskingRule,
  type Subscription,
  createMaskingRule,
  createSubscription,
  deleteMaskingRule,
  deleteSubscription,
  getChartData,
  listMaskingRules,
  listSubscriptions,
  updateDataset,
} from '@/api/dataset'

const props = defineProps<{ modelValue: boolean; dataset: Dataset | null }>()
const emit = defineEmits<{ 'update:modelValue': [boolean]; saved: [] }>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})
const tab = ref('params')

// ---- 参数 ----
const params = ref<{ name: string; label: string; default: string }[]>([])
const savingParams = ref(false)
function addParam() {
  params.value.push({ name: '', label: '', default: '' })
}
async function saveParams() {
  if (!props.dataset) return
  savingParams.value = true
  try {
    await updateDataset(props.dataset.id, { params: params.value.filter((p) => p.name) })
    ElMessage.success('参数已保存')
    emit('saved')
  } finally {
    savingParams.value = false
  }
}

// ---- 推送 ----
const subs = ref<Subscription[]>([])
const subForm = reactive({ channel: 'email', target: '' })
async function loadSubs() {
  if (!props.dataset) return
  subs.value = (await listSubscriptions(props.dataset.id)).data
}
async function addSub() {
  if (!props.dataset || !subForm.target) {
    ElMessage.warning('请填写邮箱或 Webhook 地址')
    return
  }
  await createSubscription({ dataset: props.dataset.id, channel: subForm.channel, target: subForm.target })
  subForm.target = ''
  await loadSubs()
  ElMessage.success('已添加订阅')
}
async function removeSub(id: number) {
  await deleteSubscription(id)
  await loadSubs()
}

// ---- 脱敏 ----
const rules = ref<MaskingRule[]>([])
const ruleForm = reactive({ column: '', strategy: 'partial' })
async function loadRules() {
  if (!props.dataset) return
  rules.value = (await listMaskingRules(props.dataset.id)).data
}
async function addRule() {
  if (!props.dataset || !ruleForm.column) {
    ElMessage.warning('请填写要脱敏的列名')
    return
  }
  await createMaskingRule({ dataset: props.dataset.id, column: ruleForm.column, strategy: ruleForm.strategy })
  ruleForm.column = ''
  await loadRules()
  ElMessage.success('已添加脱敏规则')
}
async function removeRule(id: number) {
  await deleteMaskingRule(id)
  await loadRules()
}

// ---- 图表 ----
const chartForm = reactive({ x: '', y: '', agg: 'sum' as 'sum' | 'count' | 'avg' })
const chart = ref<{ labels: string[]; values: number[] } | null>(null)
const chartLoading = ref(false)
const chartMax = computed(() => Math.max(1, ...(chart.value?.values ?? [])))
async function genChart() {
  if (!props.dataset || !chartForm.x) {
    ElMessage.warning('请至少填写 X 列')
    return
  }
  chartLoading.value = true
  try {
    const { data } = await getChartData(props.dataset.id, chartForm.x, chartForm.y || undefined, chartForm.agg)
    chart.value = data
  } catch {
    chart.value = null
  } finally {
    chartLoading.value = false
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (open && props.dataset) {
      tab.value = 'params'
      params.value = (props.dataset.params as never[])?.map((p: Record<string, string>) => ({
        name: p.name ?? '',
        label: p.label ?? '',
        default: p.default ?? '',
      })) ?? []
      chart.value = null
      chartForm.x = ''
      chartForm.y = ''
      loadSubs()
      loadRules()
    }
  },
)
</script>

<template>
  <el-dialog v-model="visible" :title="`数据集设置 · ${dataset?.name ?? ''}`" width="640px" top="6vh">
    <el-tabs v-model="tab">
      <!-- 参数 -->
      <el-tab-pane label="参数" name="params">
        <p class="hint">
          定义查询参数（SQL 用绑定变量引用：Oracle <code>:name</code> / MySQL
          <code>%(name)s</code>）。运行时可传入，定时运行用默认值。
        </p>
        <div v-for="(p, i) in params" :key="i" class="prow">
          <el-input v-model="p.name" placeholder="参数名 name" class="pin" />
          <el-input v-model="p.label" placeholder="显示名" class="pin" />
          <el-input v-model="p.default" placeholder="默认值" class="pin" />
          <el-button text type="danger" :icon="Delete" @click="params.splice(i, 1)" />
        </div>
        <el-button text :icon="Plus" @click="addParam">添加参数</el-button>
        <div class="foot">
          <el-button type="primary" :loading="savingParams" @click="saveParams">保存参数</el-button>
        </div>
      </el-tab-pane>

      <!-- 推送 -->
      <el-tab-pane label="推送订阅" name="subs">
        <p class="hint">数据集运行成功后推送通知。Webhook 填钉钉/企业微信机器人地址。</p>
        <div class="addrow">
          <el-select v-model="subForm.channel" class="chan">
            <el-option label="邮件" value="email" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
          <el-input
            v-model="subForm.target"
            :placeholder="subForm.channel === 'email' ? '收件邮箱' : '机器人 Webhook 地址'"
          />
          <el-button type="primary" :icon="Plus" @click="addSub">添加</el-button>
        </div>
        <ul class="rule-list">
          <li v-for="s in subs" :key="s.id">
            <el-tag size="small" :type="s.channel === 'email' ? 'info' : 'warning'">{{
              s.channel === 'email' ? '邮件' : 'Webhook'
            }}</el-tag>
            <span class="rule-target">{{ s.target }}</span>
            <el-button text type="danger" :icon="Delete" @click="removeSub(s.id)" />
          </li>
          <li v-if="!subs.length" class="empty">还没有订阅</li>
        </ul>
      </el-tab-pane>

      <!-- 脱敏 -->
      <el-tab-pane label="列脱敏" name="mask">
        <p class="hint">普通用户预览/下载时对这些列遮蔽；管理员与数据集属主看原值。</p>
        <div class="addrow">
          <el-input v-model="ruleForm.column" placeholder="列名（与表头一致）" />
          <el-select v-model="ruleForm.strategy" class="chan">
            <el-option label="部分遮蔽" value="partial" />
            <el-option label="全部遮蔽" value="full" />
          </el-select>
          <el-button type="primary" :icon="Plus" @click="addRule">添加</el-button>
        </div>
        <ul class="rule-list">
          <li v-for="r in rules" :key="r.id">
            <el-tag size="small">{{ r.column }}</el-tag>
            <span class="rule-target">{{
              r.strategy === 'full' ? '全部遮蔽' : '部分遮蔽（保留首尾）'
            }}</span>
            <el-button text type="danger" :icon="Delete" @click="removeRule(r.id)" />
          </li>
          <li v-if="!rules.length" class="empty">没有脱敏规则</li>
        </ul>
      </el-tab-pane>

      <!-- 图表 -->
      <el-tab-pane label="图表" name="chart">
        <p class="hint">对最新成功文件按 X 列分组、对 Y 列聚合，快速看分布。</p>
        <div class="addrow">
          <el-input v-model="chartForm.x" placeholder="X 列（分组）" />
          <el-input v-model="chartForm.y" placeholder="Y 列（数值，count 可空）" />
          <el-select v-model="chartForm.agg" class="chan">
            <el-option label="求和" value="sum" />
            <el-option label="计数" value="count" />
            <el-option label="平均" value="avg" />
          </el-select>
          <el-button type="primary" :loading="chartLoading" @click="genChart">生成</el-button>
        </div>
        <div v-if="chart && chart.labels.length" class="chart">
          <div v-for="(lab, i) in chart.labels" :key="i" class="crow">
            <span class="clab">{{ lab }}</span>
            <div class="ctrack">
              <div class="cfill" :style="{ width: (chart.values[i] / chartMax) * 100 + '%' }" />
            </div>
            <span class="cval">{{ chart.values[i] }}</span>
          </div>
        </div>
        <el-empty v-else-if="!chartLoading" description="填写 X/Y 列后点生成" :image-size="60" />
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<style scoped>
.hint {
  font-size: 12.5px;
  color: var(--ink-3, #889);
  margin: 0 0 14px;
  line-height: 1.6;
}
.hint code {
  background: var(--surface-2, #f9fafd);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
}
.prow {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.pin {
  flex: 1;
}
.foot {
  margin-top: 16px;
  text-align: right;
}
.addrow {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}
.chan {
  width: 130px;
  flex-shrink: 0;
}
.rule-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.rule-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--border, #e9edf4);
  border-radius: var(--r-sm, 8px);
}
.rule-target {
  flex: 1;
  font-size: 13px;
  color: var(--ink-2, #565f70);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty {
  justify-content: center;
  color: var(--ink-3, #889);
  font-size: 13px;
  border-style: dashed !important;
}
.chart {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-top: 8px;
}
.crow {
  display: grid;
  grid-template-columns: 110px 1fr 56px;
  align-items: center;
  gap: 10px;
}
.clab {
  font-size: 13px;
  color: var(--ink-2, #565f70);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ctrack {
  height: 10px;
  background: var(--surface-2, #f9fafd);
  border-radius: 999px;
  overflow: hidden;
}
.cfill {
  height: 100%;
  background: var(--accent, #4b5bd6);
  border-radius: 999px;
  transition: width var(--dur, 200ms) var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.cval {
  font-size: 13px;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
@media (prefers-reduced-motion: reduce) {
  .cfill {
    transition: none;
  }
}
</style>
