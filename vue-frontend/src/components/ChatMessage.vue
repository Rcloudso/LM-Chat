<script setup>
import { ref, computed } from 'vue';
import MarkdownIt from 'markdown-it';

// 创建markdown-it实例，优化配置
const md = new MarkdownIt({
  html: false, // 禁用HTML标签，提高安全性
  breaks: true, // 将\n转换为<br>
  linkify: true, // 自动转换URL为链接
  typographer: true, // 启用一些语言中立的替换和引号美化
});

// 组件属性定义
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

// 使用computed属性缓存渲染后的Markdown内容，避免重复渲染
const renderedContent = computed(() => md.render(props.content));

</script>

<template>
  <div v-if="role === 'system'" class="system-message">
    {{ content }}
  </div>

  <!-- 用户和助手消息的通用容器 -->
  <div v-else :class="['message', `${role}-message`, 'markdown-content']">
    <!-- 思考内容（仅助手消息且有思考内容时显示） -->
    <div v-if="role === 'assistant' && thinking" class="think-container mb-2">
      <button class="btn btn-sm btn-outline-secondary mb-1" @click="toggleThinking">
        查看思考过程 <span class="toggle-icon">{{ showThinking ? '▲' : '▼' }}</span>
      </button>
      <div v-if="thinking" :class="['think-content', { 'show': showThinking }]">
        <pre>{{ thinking }}</pre>
      </div>
    </div>

    <!-- 使用计算属性渲染Markdown内容，提高性能 -->
    <div v-html="renderedContent" class="message-content"></div>
  </div>
</template>

<style scoped>
.message-content,
.system-message,
.user-message .message-content,
.assistant-message .message-content {
  text-align: left;
}

.think-container {
  width: 100%;
}

.think-content {
  display: none;
  background-color: #f0f0f0;
  border-radius: 6px;
  padding: 8px;
  margin-top: 4px;
  font-size: 0.9em;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease-out, opacity 0.3s ease-out;
  opacity: 0;
}

.think-content.show {
  display: block;
  max-height: 300px;
  overflow-y: auto;
  opacity: 1;
}

.think-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-content :deep(pre) {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
}

.markdown-content :deep(code) {
  background-color: rgba(175, 184, 193, 0.2);
  border-radius: 6px;
  padding: 0.2em 0.4em;
  font-family: monospace;
}

.markdown-content :deep(a) {
  color: #0969da;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}
</style>