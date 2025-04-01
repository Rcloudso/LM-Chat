<script setup>
import { ref, defineEmits, defineProps, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const props = defineProps({
  isSidebarVisible: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['toggle-sidebar', 'new-chat', 'load-chat']);

// 定义状态
const historyChats = ref([]);
const selectedChatId = ref(null);

// 格式化日期
const formatChatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === now.toDateString()) {
    return '今天';
  } else if (date.toDateString() === yesterday.toDateString()) {
    return '昨天';
  } else if (now.getTime() - date.getTime() < 30 * 24 * 60 * 60 * 1000) {
    return '30 天内';
  } else {
    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
  }
};

// 加载聊天历史
const loadHistoryChats = async () => {
  try {
    const response = await axios.get('/api/chats');
    if (response.data && Array.isArray(response.data)) {
      historyChats.value = response.data.map(chat => ({
        ...chat,
        date: formatChatDate(chat.updated_at)
      }));
    }
  } catch (error) {
    console.error('加载历史对话失败:', error);
    ElMessage.error('加载历史对话失败');
  }
};

// 聊天记录选择
const selectChat = (id) => {
  selectedChatId.value = id;
  const chat = historyChats.value.find(c => c.id === id);
  if (chat) {
    emit('load-chat', id, chat.title);
  }
};

const createNewChat = () => {
  // Reset selection and trigger new chat event
  selectedChatId.value = null;
  emit('new-chat');
  
  // 加载历史对话增加延迟
  setTimeout(loadHistoryChats, 500);
};

const deleteChat = async (id, event) => {
  event.stopPropagation();

  try {
    await axios.delete(`/api/chats/${id}`);
    
    if (selectedChatId.value === id) {
      selectedChatId.value = null;
      emit('new-chat');
    }
    
    await loadHistoryChats();
    ElMessage.success('删除成功');
  } catch (error) {
    console.error('删除对话失败:', error);
    ElMessage.error('删除对话失败');
  }
};

// 展示管理员提示，未做登录
const showAdminAlert = () => {
  alert('您是管理员！');
};

onMounted(loadHistoryChats);

// 给父组件暴露方法
defineExpose({
  selectedChatId,
  createNewChat,
  loadHistoryChats
});
</script>

<template>
  <div>
    <div class="sidebar" :class="{ 'sidebar-hidden': !isSidebarVisible }">
      <div class="sidebar-header">
        <div class="logo">LM Chat</div>
        <button class="toggle-button" @click="emit('toggle-sidebar')">
          <span>☰</span>
        </button>
      </div>

      <button class="new-chat-button" @click="createNewChat">
        <i class="icon">+</i> 开启新对话
      </button>

      <div class="history-container">
        <!-- Empty state -->
        <div v-if="historyChats.length === 0" class="empty-history">
          <p>暂无历史对话</p>
        </div>

        <!-- Group chats by date category -->
        <template v-for="dateGroup in ['今天', '昨天', '30 天内']">
          <div v-if="historyChats.filter(c => c.date === dateGroup).length > 0" class="date-group" :key="dateGroup">
            <div class="date-label">{{ dateGroup }}</div>
            <div v-for="chat in historyChats.filter(c => c.date === dateGroup)" :key="chat.id"
              :class="['chat-item', { 'active': selectedChatId === chat.id }]" @click="selectChat(chat.id)">
              <span class="chat-title">{{ chat.title }}</span>
              <button class="delete-btn" @click="deleteChat(chat.id, $event)" title="删除对话">
                <span>×</span>
              </button>
            </div>
          </div>
        </template>

        <!-- Earlier chats (grouped by month) -->
        <template
          v-for="dateGroup in [...new Set(historyChats.filter(c => !['今天', '昨天', '30 天内'].includes(c.date)).map(c => c.date))]">
          <div v-if="historyChats.filter(c => c.date === dateGroup).length > 0" class="date-group" :key="dateGroup">
            <div class="date-label">{{ dateGroup }}</div>
            <div v-for="chat in historyChats.filter(c => c.date === dateGroup)" :key="chat.id"
              :class="['chat-item', { 'active': selectedChatId === chat.id }]" @click="selectChat(chat.id)">
              <span class="chat-title">{{ chat.title }}</span>
              <button class="delete-btn" @click="deleteChat(chat.id, $event)" title="删除对话">
                <span>×</span>
              </button>
            </div>
          </div>
        </template>
      </div>

      <div class="sidebar-footer">
        <button class="user-profile" @click="showAdminAlert">
          <i class="icon">👤</i> 个人信息
        </button>
      </div>
    </div>

    <button v-if="!isSidebarVisible" class="expand-button" @click="emit('toggle-sidebar')">
      <span>☰</span>
    </button>
  </div>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  width: 240px;
  height: 100vh;
  background-color: #f9f9f9;
  border-right: 1px solid #e5e7eb;
  color: #333;
  transition: transform 0.3s ease;
  position: relative;
  z-index: 5;
}

.sidebar-hidden {
  transform: translateX(-100%);
}

.expand-button {
  position: fixed;
  left: 0;
  top: 16px;
  z-index: 10;
  background-color: #f9f9f9;
  border: 1px solid #e5e7eb;
  border-left: none;
  border-radius: 0 4px 4px 0;
  padding: 8px 12px;
  font-size: 16px;
  color: #666;
  cursor: pointer;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
}

.expand-button:hover {
  background-color: #f0f0f0;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.logo {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.toggle-button {
  font-size: 16px;
  color: #666;
  cursor: pointer;
  background: none;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
}

.toggle-button:hover {
  background-color: #f0f0f0;
}

.new-chat-button {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 16px;
  padding: 8px 16px;
  background-color: #f0f0f0;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.new-chat-button:hover {
  background-color: #e5e5e5;
}

.icon {
  margin-right: 8px;
}

.history-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.date-group {
  margin-bottom: 16px;
}

.date-label {
  padding: 8px 8px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.chat-item {
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.chat-item:hover {
  background-color: #f0f0f0;
}

.chat-item.active {
  background-color: #e6f7ff;
  color: #1890ff;
}

.delete-btn {
  visibility: hidden;
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
  margin-left: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

.chat-item:hover .delete-btn {
  visibility: visible;
}

.delete-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
  color: #ff4d4f;
}

.empty-history {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.user-profile {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px;
  margin-bottom: 8px;
  background: none;
  border: none;
  text-align: left;
  font-size: 14px;
  color: #333;
  cursor: pointer;
}

.user-profile:hover {
  background-color: #f0f0f0;
  border-radius: 6px;
}

@media (max-width: 992px) {
  .sidebar {
    width: 220px;
  }
}

@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    left: 0;
    top: 0;
    width: 240px;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  }
}

@media (max-width: 576px) {
  .sidebar {
    width: 100%;
    max-width: 280px;
  }

  .new-chat-button {
    margin: 12px;
  }

  .sidebar-footer {
    padding: 12px;
  }
}
</style>