<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  loading: boolean
}>()

const emit = defineEmits<{
  search: [url: string]
}>()

const inputUrl = ref('')

const handleSearch = () => {
  if (inputUrl.value.trim()) {
    emit('search', inputUrl.value.trim())
  }
}
</script>

<template>
  <div class="search-box">
    <input
      v-model="inputUrl"
      type="text"
      class="search-input"
      placeholder="输入UP主主页链接，如：https://www.douyin.com/user/MS4wLjABAAAA..."
      :disabled="loading"
      @keyup.enter="handleSearch"
    />
    <button
      class="search-btn"
      :disabled="loading || !inputUrl.trim()"
      @click="handleSearch"
    >
      {{ loading ? '查询中...' : '查询' }}
    </button>
  </div>
</template>
