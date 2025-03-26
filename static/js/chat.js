document.addEventListener('DOMContentLoaded', function () {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const streamToggle = document.getElementById('stream-toggle');
    const temperatureSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('temp-value');
    const maxTokensSlider = document.getElementById('max-tokens');
    const tokensValue = document.getElementById('tokens-value');

    // 存储聊天历史
    let chatHistory = [];

    // 更新滑块值显示
    temperatureSlider.addEventListener('input', function () {
        tempValue.textContent = this.value;
    });

    maxTokensSlider.addEventListener('input', function () {
        tokensValue.textContent = this.value;
    });

    // 发送消息函数
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // 添加用户消息到聊天界面
        addMessageToChat('user', message);

        // 清空输入框
        userInput.value = '';

        // 添加用户消息到历史记录
        chatHistory.push({ role: 'user', content: message });

        // 显示加载指示器
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'typing-indicator';
        loadingIndicator.innerHTML = '<span></span><span></span><span></span>';
        chatContainer.appendChild(loadingIndicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // 准备请求参数
        const requestData = {
            messages: chatHistory,
            temperature: parseFloat(temperatureSlider.value),
            max_tokens: parseInt(maxTokensSlider.value),
            stream: streamToggle.checked
        };

        // 发送请求到后端
        if (streamToggle.checked) {
            // 流式响应处理
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            }).then(response => {
                if (!response.ok) {
                    throw new Error('API请求失败: ' + response.statusText);
                }

                // 创建消息容器
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message assistant-message';
                chatContainer.appendChild(messageDiv);

                // 移除加载指示器
                loadingIndicator.remove();

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let assistantMessage = '';

                return new ReadableStream({
                    start(controller) {
                        let isConnected = true;
                        let isClosing = false;
                        let retryCount = 0;
                        const MAX_RETRIES = 3;

                        function handleStreamError(error) {
                            console.error('流式处理出错:', error);
                            if (!isClosing) {
                                if (retryCount < MAX_RETRIES && isConnected) {
                                    retryCount++;
                                    console.log(`尝试重新连接 (${retryCount}/${MAX_RETRIES})...`);
                                    setTimeout(() => push(), 1000 * retryCount); // 递增重试延迟
                                } else {
                                    isClosing = true;
                                    addSystemMessage(`连接中断: ${error.message}`);
                                    controller.error(error);
                                }
                            }
                        }

                        async function push() {
                            try {
                                if (!isConnected || isClosing) {
                                    return;
                                }

                                const { done, value } = await reader.read();

                                if (done) {
                                    if (!isClosing) {
                                        isConnected = false;
                                        isClosing = true;
                                        controller.close();
                                        chatHistory.push({ role: 'assistant', content: assistantMessage });
                                    }
                                    return;
                                }

                                const chunk = decoder.decode(value, { stream: true });
                                const lines = chunk.split('\n');

                                for (const line of lines) {
                                    if (line.startsWith('data: ')) {
                                        try {
                                            const jsonStr = line.slice(5).trim();
                                            if (!jsonStr) {
                                                console.warn('Empty JSON string received');
                                                continue;
                                            }
                                            
                                            // 尝试修复可能的JSON格式问题
                                            let fixedJsonStr = jsonStr;
                                            // 处理可能的未闭合引号或括号
                                            try {
                                                // 先尝试解析原始JSON
                                                const data = JSON.parse(fixedJsonStr);
                                                if (data.choices && data.choices[0] && data.choices[0].delta && data.choices[0].delta.content) {
                                                    const content = data.choices[0].delta.content;
                                                    assistantMessage += content;
                                                    messageDiv.textContent = assistantMessage;
                                                    chatContainer.scrollTop = chatContainer.scrollHeight;
                                                } else if (data.error) {
                                                    throw new Error(data.error);
                                                }
                                            } catch (parseError) {
                                                // 如果解析失败，记录错误但不中断流程
                                                console.warn('JSON解析警告:', parseError.message, '\n原始数据:', jsonStr);
                                                // 尝试提取文本内容（如果存在）
                                                const contentMatch = jsonStr.match(/"content"\s*:\s*"([^"]*)"/i);
                                                if (contentMatch && contentMatch[1]) {
                                                    const extractedContent = contentMatch[1];
                                                    assistantMessage += extractedContent;
                                                    messageDiv.textContent = assistantMessage;
                                                    chatContainer.scrollTop = chatContainer.scrollHeight;
                                                }
                                            }
                                        } catch (e) {
                                            console.error('处理流数据错误:', e.message, '\n原始数据:', line.slice(5));
                                            // 记录错误但不立即中断连接，除非是严重错误
                                            if (e.message.includes('SyntaxError') || retryCount >= MAX_RETRIES) {
                                                handleStreamError(new Error('数据处理失败: ' + e.message));
                                                return;
                                            }
                                        }
                                    }
                                }

                                controller.enqueue(value);
                                push();
                            } catch (error) {
                                handleStreamError(error);
                            }
                        }

                        push();
                    }
                });
            })
                .catch(error => {
                    // 移除加载指示器
                    loadingIndicator.remove();

                    // 显示错误消息
                    console.error('Error:', error);
                    addSystemMessage('发生错误: ' + error.message);
                });
        } else {
            // 非流式响应处理
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('API请求失败: ' + response.statusText);
                    }
                    return response.json();
                })
                .then(data => {
                    // 移除加载指示器
                    loadingIndicator.remove();

                    // 处理响应
                    if (data.choices && data.choices.length > 0) {
                        const assistantMessage = data.choices[0].message.content;
                        addMessageToChat('assistant', assistantMessage);

                        // 添加助手消息到历史记录
                        chatHistory.push({ role: 'assistant', content: assistantMessage });
                    }
                })
                .catch(error => {
                    // 移除加载指示器
                    loadingIndicator.remove();

                    // 显示错误消息
                    console.error('Error:', error);
                    addSystemMessage('发生错误: ' + error.message);
                });
        }
    }

    // 添加消息到聊天界面
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message markdown-content`;

        // 检查是否包含<think>标签
        const thinkMatch = content.match(/<think>(.*?)<\/think>/s);
        if (thinkMatch) {
            // 提取思考内容和实际回复
            const thinkContent = thinkMatch[1].trim();
            const actualContent = content.replace(/<think>.*?<\/think>/s, '').trim();

            // 创建折叠组件
            const thinkDiv = document.createElement('div');
            thinkDiv.className = 'think-container mb-2';

            // 创建折叠按钮
            const toggleButton = document.createElement('button');
            toggleButton.className = 'btn btn-sm btn-outline-secondary mb-1';
            toggleButton.innerHTML = '查看思考过程 <span class="toggle-icon">▼</span>';

            // 创建思考内容容器
            const thinkContentDiv = document.createElement('div');
            thinkContentDiv.className = 'think-content collapse';
            thinkContentDiv.textContent = thinkContent;

            // 添加点击事件
            toggleButton.addEventListener('click', function () {
                const isCollapsed = thinkContentDiv.classList.contains('show');
                if (isCollapsed) {
                    thinkContentDiv.classList.remove('show');
                    toggleButton.querySelector('.toggle-icon').textContent = '▼';
                } else {
                    thinkContentDiv.classList.add('show');
                    toggleButton.querySelector('.toggle-icon').textContent = '▲';
                }
            });

            // 组装折叠组件
            thinkDiv.appendChild(toggleButton);
            thinkDiv.appendChild(thinkContentDiv);

            // 添加到消息div
            messageDiv.appendChild(thinkDiv);

            // 添加实际回复
            const responseDiv = document.createElement('div');
            responseDiv.textContent = actualContent;
            messageDiv.appendChild(responseDiv);
        } else {
            messageDiv.textContent = content;
        }

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 添加系统消息
    function addSystemMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'system-message';
        messageDiv.textContent = message;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 事件监听器
    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});