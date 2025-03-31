<script setup>
import { ref } from 'vue';
import MarkdownIt from 'markdown-it';

// 创建markdown-it实例
const md = new MarkdownIt({
  html: false, // 禁用HTML标签
  breaks: true, // 将\n转换为<br>
  linkify: true, // 自动转换URL为链接
});

const props = defineProps({
  role: {
    type: String,
    required: true,
    validator: (value) => ['user', 'assistant', 'system'].includes(value)
  },
  content: {
    type: String,
    required: true
  },
  thinking: {
    type: String,
    default: ''
  }
});

const showThinking = ref(false);

const toggleThinking = () => {
  showThinking.value = !showThinking.value;
};
</script>

<template>
  <div :class="['message', `${role}-message`, 'markdown-content']">
    <!-- 思考内容（仅助手消息且有思考内容时显示） -->
    <div v-if="role === 'assistant' && thinking" class="think-container mb-2">
      <button class="btn btn-sm btn-outline-secondary mb-1" @click="toggleThinking">
        查看思考过程 <span class="toggle-icon">{{ showThinking ? '▲' : '▼' }}</span>
      </button>
      <div :class="['think-content', { 'show': showThinking }]">
        {{ thinking }}
      </div>
    </div>
    
    <!-- 消息内容 -->
    <div v-html="md.render(content)"></div>
  </div>
  
  <!-- 系统消息使用不同的样式 -->
  <div v-if="role === 'system'" class="system-message">
    {{ content }}
  </div>
</template>

<style scoped>
/* 样式将从全局CSS中继承 */
</style>