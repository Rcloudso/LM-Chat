<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import axios from 'axios';
import ChatMessage from './ChatMessage.vue';

// 响应式状态
const chatHistory = ref([]);
const userInput = ref('');
const isStreaming = ref(true);
const temperature = ref(0.7);
const maxTokens = ref(2048);
const isLoading = ref(false);

// 添加系统欢迎消息
onMounted(() => {
  chatHistory.value.push({
    role: 'system',
    content: '欢迎使用LM Studio本地大模型对话系统，请输入您的问题。'
  });
});

// 发送消息
const sendMessage = async () => {
  const message = userInput.value.trim();
  if (!message) return;

  // 添加用户消息到聊天历史
  chatHistory.value.push({
    role: 'user',
    content: message
  });

  // 清空输入框
  userInput.value = '';

  // 设置加载状态
  isLoading.value = true;

  // 准备请求参数
  const requestData = {
    messages: chatHistory.value.filter(msg => msg.role !== 'system'),
    temperature: temperature.value,
    max_tokens: maxTokens.value,
    stream: isStreaming.value
  };

  try {
    if (isStreaming.value) {
      // 流式响应处理
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.statusText}`);
      }

      // 创建临时消息对象
      const tempMessage = {
        role: 'assistant',
        content: ''
      };
      chatHistory.value.push(tempMessage);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(5).trim();
              if (jsonStr === '[DONE]') continue;
              if (!jsonStr) continue;

              const data = JSON.parse(jsonStr);
              if (data.choices && data.choices[0] && data.choices[0].delta && data.choices[0].delta.content) {
                const content = data.choices[0].delta.content;
                tempMessage.content += content;
              } else if (data.error) {
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('处理流数据错误:', e.message);
            }
          }
        }
      }
    } else {
      // 非流式响应处理
      const response = await axios.post('/api/chat', requestData);
      const data = response.data;

      if (data.choices && data.choices.length > 0) {
        const assistantMessage = data.choices[0].message.content;
        chatHistory.value.push({
          role: 'assistant',
          content: assistantMessage
        });
      }
    }
  } catch (error) {
    console.error('Error:', error);
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
      <div class="card-header">
        <h3 class="mb-0">LM Studio 本地大模型对话</h3>
      </div>
      <div class="card-body">
        <!-- 聊天消息容器 -->
        <div id="chat-container" class="mb-3">
          <ChatMessage 
            v-for="(message, index) in chatHistory" 
            :key="index"
            :role="message.role"
            :content="message.content"
            :thinking="message.thinking || ''"
          />
          
          <!-- 加载指示器 -->
          <div v-if="isLoading" class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="input-group">
          <input 
            type="text" 
            v-model="userInput" 
            class="form-control" 
            placeholder="输入您的问题..."
            @keyup.enter="sendMessage"
          >
          <button 
            class="btn btn-primary" 
            type="button" 
            @click="sendMessage"
            :disabled="isLoading || !userInput.trim()"
          >
            发送
          </button>
        </div>
        
        <!-- 设置区域 -->
        <div class="mt-3">
          <div class="form-check form-switch">
            <input 
              class="form-check-input" 
              type="checkbox" 
              id="stream-toggle"
              v-model="isStreaming"
            >
            <label class="form-check-label" for="stream-toggle">流式输出</label>
          </div>
          
          <div class="row mt-2">
            <div class="col-md-6">
              <label for="temperature" class="form-label">
                温度: <span>{{ temperature }}</span>
              </label>
              <input 
                type="range" 
                class="form-range" 
                min="0" 
                max="1" 
                step="0.1" 
                v-model="temperature"
              >
            </div>
            <div class="col-md-6">
              <label for="max-tokens" class="form-label">
                最大生成长度: <span>{{ maxTokens }}</span>
              </label>
              <input 
                type="range" 
                class="form-range" 
                min="128" 
                max="4096" 
                step="128" 
                v-model="maxTokens"
              >
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

/* 响应式布局 */
@media (max-width: 992px) {
  .chat-interface {
    padding: 10px;
  }
  
  .card-header h3 {
    font-size: 1.1rem;
  }
}

@media (max-width: 768px) {
  .row {
    flex-direction: column;
  }
  
  .col-md-6 {
    width: 100%;
    margin-bottom: 10px;
  }
}

@media (max-width: 576px) {
  .chat-interface {
    padding: 5px;
  }
  
  .card-body {
    padding: 10px;
  }
  
  .input-group {
    flex-direction: column;
  }
  
  .input-group input {
    width: 100%;
    margin-bottom: 8px;
    border-radius: 4px;
  }
  
  .btn-primary {
    width: 100%;
    border-radius: 4px;
  }
}
</style>