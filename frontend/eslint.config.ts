import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'
import pluginVue from 'eslint-plugin-vue'

// ESLint 扁平配置：Vue 3 + TypeScript 官方推荐，格式交给 Prettier
export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,tsx,vue}'],
  },
  {
    name: 'app/files-to-ignore',
    ignores: ['dist/**', 'node_modules/**'],
  },
  pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,
  skipFormatting,
)
