<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import axios from 'axios';
import ChatMessage from './ChatMessage.vue';

// 响应式状态
const chatHistory = ref([]);
const userInput = ref('');
const isStreaming = ref(true);
const temperature = ref(0.8);
const maxTokens = ref(2048);
const isLoading = ref(false);

// 定义方法供父组件设置待发送消息
const setPendingMessage = (message) => {
  userInput.value = message;
  sendMessage();
};

// 暴露方法给父组件
defineExpose({
  setPendingMessage
});

// 聊天容器引用
const chatContainer = ref(null);

// 添加系统欢迎消息
onMounted(() => {
  chatHistory.value.push({
    role: 'assistant',
    content: '欢迎使用LM Chat，请输入您的问题。'
  });
});

// 监听聊天历史变化，自动滚动到底部
watch(chatHistory, () => {
  nextTick(() => {
    scrollToBottom();
  });
}, { deep: true });

// 滚动到底部
const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

// 清空聊天历史
const clearChat = () => {
  chatHistory.value = [];
  // 添加欢迎消息
  chatHistory.value.push({
    role: 'assistant',
    content: '聊天已清空，请输入新的问题。'
  });
};

// 处理流式响应
const handleStreamResponse = async (response) => {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  // 添加一个新的消息到聊天历史
  const messageIndex = chatHistory.value.length;
  chatHistory.value.push({ role: 'assistant', content: '' });
  const assistantMessage = chatHistory.value[messageIndex];

  // 创建渲染控制器
  let renderQueue = [];
  let animationFrameId = null;
  
  const render = () => {
    if (renderQueue.length > 0) {
      assistantMessage.content += renderQueue.join('');
      renderQueue = [];
    }
    animationFrameId = requestAnimationFrame(render);
  };
  animationFrameId = requestAnimationFrame(render);
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      const lines = chunk.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;

        const jsonStr = line.slice(6).trim();
        if (jsonStr === '[DONE]' || !jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);
          if (data.choices?.[0]?.delta?.content) {
            renderQueue.push(data.choices[0].delta.content);
          } else if (data.error) {
            throw new Error(data.error);
          }
        } catch (e) {
          console.error('处理流数据错误:', e.message);
        }
      }
    }
    
    // 处理最后可能剩余的buffer数据
    if (buffer && buffer.startsWith('data: ')) {
      try {
        const jsonStr = buffer.slice(6).trim();
        if (jsonStr && jsonStr !== '[DONE]') {
          const data = JSON.parse(jsonStr);
          if (data.choices?.[0]?.delta?.content) {
            renderQueue.push(data.choices[0].delta.content);
          }
        }
      } catch (e) {
        console.error('处理最后的buffer数据错误:', e);
      }
    }
  } catch (e) {
    console.error('处理流数据错误:', e);
    assistantMessage.content += '\n[流式响应中断]';
  } finally {
    // 确保在函数结束时取消动画帧，防止内存泄漏
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
  }
};

// 处理非流式响应
const handleNonStreamResponse = async (requestData) => {
  try {
    const response = await axios.post('/api/chat', requestData);
    const data = response.data;

    if (data.choices?.[0]?.message?.content) {
      chatHistory.value.push({
        role: 'assistant',
        content: data.choices[0].message.content
      });
    } else {
      throw new Error('响应数据格式不正确');
    }
  } catch (error) {
    console.error('非流式响应错误:', error);
    throw error; // 向上传递错误，由sendMessage统一处理
  }
};

// 发送消息
const sendMessage = async () => {
  // 验证并处理用户输入
  const message = userInput.value.trim();
  if (!message) return;
  
  // 防止XSS攻击的简单处理
  const sanitizedMessage = message
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // 添加用户消息到聊天历史
  chatHistory.value.push({ role: 'user', content: sanitizedMessage });
  userInput.value = '';
  isLoading.value = true;

  // 准备请求数据
  const requestData = {
    messages: chatHistory.value.filter(msg => msg.role !== 'system'),
    temperature: Number(temperature.value), // 确保是数字类型
    max_tokens: Number(maxTokens.value), // 确保是数字类型
    stream: isStreaming.value
  };

  // 添加一个临时的加载消息
  const loadingMessageIndex = chatHistory.value.length;
  chatHistory.value.push({ role: 'assistant', content: '...', isLoading: true });

  try {
    if (isStreaming.value) {
      // 使用fetch API处理流式响应
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });

      // 检查响应状态
      if (!response.ok) {
        throw new Error(`API请求失败: ${response.statusText}`);
      }

      // 移除加载消息
      chatHistory.value.pop();
      await handleStreamResponse(response);
    } else {
      // 移除加载消息并处理非流式响应
      chatHistory.value.pop();
      await handleNonStreamResponse(requestData);
    }
  } catch (error) {
    console.error('消息发送错误:', error);
    
    // 移除加载消息（如果还存在）
    if (chatHistory.value[loadingMessageIndex]?.isLoading) {
      chatHistory.value.pop();
    }
    
    // 显示错误消息
    ElMessage.error(`发生错误: ${error.message}`);
    chatHistory.value.push({
      role: 'system',
      content: `发生错误: ${error.message}`
    });
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="chat-interface">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h3 class="mb-0">LM Chat</h3>
        <button class="btn btn-sm btn-outline-secondary" @click="clearChat" title="清空聊天历史">
          清空
        </button>
      </div>
      <div class="card-body">
        <!-- 聊天消息容器 -->
        <div id="chat-container" class="mb-3" ref="chatContainer">
          <ChatMessage v-for="(message, index) in chatHistory" :key="index" :role="message.role"
            :content="message.content" :thinking="message.thinking || ''" />
        </div>

        <!-- 输入区域 -->
        <div class="input-group">
          <input type="text" v-model="userInput" class="form-control" placeholder="输入您的问题..."
            @keyup.enter="sendMessage">
          <button class="btn btn-primary" type="button" @click="sendMessage" :disabled="isLoading || !userInput.trim()">
            发送
          </button>
        </div>

        <!-- 设置区域 -->
        <div class="mt-3">
          <div class="settings-row">
            <!-- 流式输出开关 -->
            <div class="settings-item">
              <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="stream-toggle" v-model="isStreaming">
                <label class="form-check-label" for="stream-toggle">流式输出</label>
              </div>
            </div>

            <!-- 温度滑块 -->
            <div class="settings-item">
              <label for="temperature" class="form-label">
                温度: <span>{{ temperature }}</span>
              </label>
              <input type="range" class="form-range" min="0" max="1" step="0.1" v-model="temperature">
            </div>

            <!-- 最大生成长度滑块 -->
            <div class="settings-item">
              <label for="max-tokens" class="form-label">
                最大生成长度: <span>{{ maxTokens }}</span>
              </label>
              <input type="range" class="form-range" min="128" max="4096" step="128" v-model="maxTokens">
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 15px;
}

.card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

#chat-container {
  flex: 1;
  overflow-y: auto;
}

/* 设置区域样式 */
.settings-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
}

.settings-item {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-range {
  flex: 1;
  min-width: 100px;
  max-width: 200px;
}

.form-check-label {
  white-space: nowrap;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  white-space: nowrap;
}

/* 响应式布局 */
@media (max-width: 992px) {
  .chat-interface {
    padding: 10px;
  }

  .card-header h3 {
    font-size: 1.1rem;
  }

  .settings-item {
    min-width: 150px;
  }
}

@media (max-width: 576px) {
  .chat-interface {
    padding: 5px;
  }

  .card-body {
    padding: 10px;
  }

  .settings-row {
    flex-direction: column;
    align-items: stretch;
  }

  .settings-item {
    width: 100%;
  }

  .form-range {
    max-width: none;
  }

  .input-group {
    flex-direction: column;
  }

  .input-group input,
  .btn-primary {
    width: 100%;
    margin-bottom: 8px;
    border-radius: 4px;
  }
}
</style>