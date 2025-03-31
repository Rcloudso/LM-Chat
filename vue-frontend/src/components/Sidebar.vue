<script setup>
import { ref, defineEmits, defineProps } from 'vue';

// 定义属性
const props = defineProps({
  isSidebarVisible: {
    type: Boolean,
    default: true
  }
});

// 定义事件
const emit = defineEmits(['toggle-sidebar']);

// 模拟历史对话数据
const historyChats = ref([
  {
    id: 1,
    title: '微信生日祝福模板设计',
    date: '昨天'
  },
  {
    id: 2,
    title: 'BOSS直聘测试工程师招聘技巧',
    date: '30 天内'
  },
  {
    id: 3,
    title: '婚礼父母感谢词简洁温馨模板',
    date: '30 天内'
  },
  {
    id: 4,
    title: '婚礼献花给父母致辞建议',
    date: '30 天内'
  },
  {
    id: 5,
    title: '宝玉珠测试工程师简历优化建议',
    date: '30 天内'
  },
  {
    id: 6,
    title: '而且也不是一次，我之前没得病',
    date: '30 天内'
  },
  {
    id: 7,
    title: '婚前工作态度与纪律问题反映处理',
    date: '30 天内'
  },
  {
    id: 8,
    title: '写给媳妇的情书与思念信',
    date: '2025-02'
  },
  {
    id: 9,
    title: '新郎父亲结婚典礼讲话稿',
    date: '2025-02'
  }
]);

// 当前选中的对话ID
const selectedChatId = ref(null);

// 选择对话
const selectChat = (id) => {
  selectedChatId.value = id;
  // 这里可以触发事件通知父组件加载对应的聊天记录
};

// 新建对话
const createNewChat = () => {
  // 这里可以触发事件通知父组件创建新对话
  selectedChatId.value = null;
};

// 暴露给父组件的方法和属性
defineExpose({
  selectedChatId,
  createNewChat
});
</script>

<template>
  <div>
    <!-- 侧边栏主体 -->
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
      <div class="date-group">
        <div class="date-label">昨天</div>
        <div 
          v-for="chat in historyChats.filter(c => c.date === '昨天')" 
          :key="chat.id"
          :class="['chat-item', { 'active': selectedChatId === chat.id }]"
          @click="selectChat(chat.id)"
        >
          {{ chat.title }}
        </div>
      </div>
      
      <div class="date-group">
        <div class="date-label">30 天内</div>
        <div 
          v-for="chat in historyChats.filter(c => c.date === '30 天内')" 
          :key="chat.id"
          :class="['chat-item', { 'active': selectedChatId === chat.id }]"
          @click="selectChat(chat.id)"
        >
          {{ chat.title }}
        </div>
      </div>
      
      <div class="date-group">
        <div class="date-label">2025-02</div>
        <div 
          v-for="chat in historyChats.filter(c => c.date === '2025-02')" 
          :key="chat.id"
          :class="['chat-item', { 'active': selectedChatId === chat.id }]"
          @click="selectChat(chat.id)"
        >
          {{ chat.title }}
        </div>
      </div>
    </div>
    
    <div class="sidebar-footer">
      <button class="app-download">
        <i class="icon">📱</i> 下载 App <span class="new-badge">NEW</span>
      </button>
      <button class="user-profile">
        <i class="icon">👤</i> 个人信息
      </button>
    </div>
  </div>
  
  <!-- 侧边栏收起时显示的展开按钮 -->
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-item:hover {
  background-color: #f0f0f0;
}

.chat-item.active {
  background-color: #e6f7ff;
  color: #1890ff;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.app-download, .user-profile {
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

.app-download:hover, .user-profile:hover {
  background-color: #f0f0f0;
  border-radius: 6px;
}

.new-badge {
  background-color: #ff4d4f;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: 8px;
}

/* 响应式布局 */
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