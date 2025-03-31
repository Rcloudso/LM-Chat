<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import Sidebar from './Sidebar.vue';
import ChatInterface from './ChatInterface.vue';

// 控制是否显示聊天界面（首次访问显示欢迎页面，开始对话后显示聊天界面）
const showChatInterface = ref(false);

// 当前选中的对话标题
const currentChatTitle = ref('');

// 控制侧边栏显示/隐藏
const showSidebar = ref(true);

// 根据窗口宽度自动设置侧边栏状态
const handleResize = () => {
  showSidebar.value = window.innerWidth > 768;
};

// 切换侧边栏显示/隐藏
const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value;
};

// 开始新对话
const startNewChat = () => {
  showChatInterface.value = true;
  currentChatTitle.value = '';
};

// 加载历史对话
const loadHistoryChat = (chatId, title) => {
  showChatInterface.value = true;
  currentChatTitle.value = title;
  // 这里可以添加加载历史对话的逻辑
};

// 监听窗口大小变化
onMounted(() => {
  handleResize();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});
</script>

<template>
  <div class="home-container">
    <!-- 侧边栏 -->
    <div class="sidebar-container">
      <Sidebar :isSidebarVisible="showSidebar" @new-chat="startNewChat" @load-chat="loadHistoryChat" @toggle-sidebar="toggleSidebar" />
    </div>
    
    <!-- 主内容区域 -->
    <div class="main-content" :class="{ 'full-width': !showSidebar }">
      <!-- 欢迎页面 -->
      <div v-if="!showChatInterface" class="welcome-page">
        <div class="welcome-content">
          <div class="welcome-icon">🤖</div>
          <h1 class="welcome-title">我是 LM Chat, 很高兴见到你!</h1>
          <p class="welcome-description">我可以帮你写代码、读文件、写作各种创意内容，请把你的任务交给我吧~</p>
          
          <div class="input-container">
            <input 
              type="text" 
              class="welcome-input" 
              placeholder="给 LM  发送消息"
              @focus="startNewChat"
            >
            <div class="input-actions">
              <button class="action-button">
                <span class="action-icon">🔍</span> 示意思考 (R1)
              </button>
              <button class="action-button">
                <span class="action-icon">🌐</span> 联网搜索
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 聊天界面 -->
      <div v-else class="chat-page">
        <div v-if="currentChatTitle" class="chat-header">
          {{ currentChatTitle }}
        </div>
        <ChatInterface />
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  display: flex;
  width: 100%;
  height: 100vh;
  background-color: #ffffff;
  position: relative;
  overflow: hidden;
}

.sidebar-container {
  position: relative;
  z-index: 10;
  transition: transform 0.3s ease;
}


.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
}

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

.input-container {
  width: 100%;
  margin-top: 20px;
}

.welcome-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 16px;
  margin-bottom: 12px;
}

.welcome-input:focus {
  outline: none;
  border-color: #6f9dec;
  box-shadow: 0 0 0 2px rgba(111, 157, 236, 0.2);
}

.input-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.action-button {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
}

.action-button:hover {
  background-color: #e9e9e9;
}

.action-icon {
  margin-right: 6px;
}

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 12px 20px;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
  background-color: #ffffff;
}

/* 响应式布局 */
@media (max-width: 992px) {
  .welcome-content {
    max-width: 90%;
  }
  
  .input-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .action-button {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .sidebar-container {
    position: absolute;
    height: 100%;
    left: 0;
    top: 0;
  }
  
  .full-width {
    margin-left: 0;
  }
  
  .welcome-content {
    padding: 0 15px;
  }
}

@media (max-width: 576px) {
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-description {
    font-size: 14px;
  }
  
  .welcome-input {
    padding: 10px 12px;
  }
}
</style>