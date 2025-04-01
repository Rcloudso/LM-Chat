<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import Sidebar from './Sidebar.vue';
import ChatInterface from './ChatInterface.vue';

// 组件状态管理
const chatState = ref({
  show: false,
  title: ''
});
const sidebarVisible = ref(window.innerWidth > 768);
const inputText = ref('');

// 组件引用
const chatRef = ref(null);
const sidebarRef = ref(null);

// 侧边栏控制
const toggleSidebar = () => sidebarVisible.value = !sidebarVisible.value;

// 聊天界面控制
const chatActions = {
  // 开始新对话
  start: () => {
    chatState.value.show = true;
    chatState.value.title = '';
  },
  
  // 重置对话
  reset: () => {
    chatState.value.show = false;
    chatState.value.title = '';
    inputText.value = '';
  },
  
  // 加载历史对话
  loadHistory: (chatId, title) => {
    chatState.value.show = true;
    chatState.value.title = title;
    nextTick(() => chatRef.value?.loadChatHistory(chatId));
  },
  
  // 处理输入发送
  sendInput: () => {
    if (!inputText.value.trim()) return;
    
    chatActions.start();
    
    nextTick(() => {
      chatRef.value?.setPendingMessage(inputText.value);
      inputText.value = '';
      
      // 延迟刷新侧边栏历史对话列表
      setTimeout(() => sidebarRef.value?.loadHistoryChats(), 1000);
    });
  }
};

// 响应式布局处理
const handleResize = () => sidebarVisible.value = window.innerWidth > 768;

// 侧边栏刷新处理
const refreshSidebar = () => sidebarRef.value?.loadHistoryChats();

// 生命周期钩子
onMounted(() => {
  handleResize();
  window.addEventListener('resize', handleResize);
  window.addEventListener('refresh-sidebar', refreshSidebar);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  window.removeEventListener('refresh-sidebar', refreshSidebar);
});
</script>

<template>
  <div class="home-container">
    <!-- 侧边栏 -->
    <div class="sidebar-container" :class="{ 'visible': sidebarVisible }">
      <Sidebar ref="sidebarRef" :isSidebarVisible="sidebarVisible" 
        @new-chat="chatActions.reset" 
        @load-chat="chatActions.loadHistory" 
        @toggle-sidebar="toggleSidebar" />
    </div>

    <!-- 主内容区域 -->
    <div class="main-content" :class="{ 'full-width': !sidebarVisible }">
      <!-- 欢迎页面 -->
      <div v-if="!chatState.show" class="welcome-page">
        <div class="welcome-content">
          <div class="welcome-icon">🤖</div>
          <h1 class="welcome-title">我是 LM Chat, 很高兴见到你!</h1>
          <p class="welcome-description">我可以帮你写代码、读文件、写作各种创意内容，请把你的任务交给我吧~</p>

          <div class="input-container">
            <input type="text" class="welcome-input" placeholder="给 LM Chat 发送消息" v-model="inputText">
            <button class="btn btn-primary send-button" @click="chatActions.sendInput" :disabled="!inputText.trim()">
              发送
            </button>
          </div>
        </div>
      </div>

      <!-- 聊天界面 -->
      <div v-else class="chat-page">
        <div v-if="chatState.title" class="chat-header">
          {{ chatState.title }}
        </div>
        <ChatInterface ref="chatRef" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 布局容器 */
.home-container {
  display: flex;
  width: 100%;
  height: 100vh;
  background-color: #ffffff;
  position: relative;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar-container {
  position: relative;
  z-index: 10;
  transition: transform 0.3s ease;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 欢迎页面 */
.welcome-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.welcome-content {
  max-width: 600px;
  text-align: center;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.welcome-title {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.welcome-description {
  font-size: 16px;
  color: #666;
  margin-bottom: 32px;
  line-height: 1.5;
}

/* 输入区域 */
.input-container {
  width: 100%;
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.welcome-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 16px;
  height: 48px;
  box-sizing: border-box;
}

.welcome-input:focus {
  outline: none;
  border-color: #6f9dec;
  box-shadow: 0 0 0 2px rgba(111, 157, 236, 0.2);
}

/* 按钮样式 */
.send-button {
  height: 48px;
  padding: 0 20px;
  border-radius: 8px;
  font-size: 16px;
  background-color: #3838cc;
  color: white;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.send-button:hover {
  background-color: #2d2db3;
}

.send-button:disabled {
  background-color: #a0a0a0;
  cursor: not-allowed;
}

/* 聊天界面 */
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #333;
  background-color: #f9fafb;
}

.full-width {
  margin-left: 0;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .sidebar-container {
    position: absolute;
    height: 100%;
    z-index: 1000;
    transform: translateX(-100%);
  }

  .sidebar-container.visible {
    transform: translateX(0);
  }

  .main-content {
    margin-left: 0;
  }
}
</style>