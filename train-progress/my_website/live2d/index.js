// index.js

// --- 角色与模型数据 (保持不变) ---
const roleData = [
    {
        name: "22娘",
        path: "./model/22/",
        outfits: [
            "model.default.json", "model.2016.xmas.1.json", "model.2016.xmas.2.json",
            "model.2017.cba-normal.json", "model.2017.cba-super.json", "model.2017.newyear.json",
            "model.2017.school.json", "model.2017.summer.normal.1.json", "model.2017.summer.normal.2.json",
            "model.2017.summer.super.1.json", "model.2017.summer.super.2.json", "model.2017.tomo-bukatsu.high.json",
            "model.2017.tomo-bukatsu.low.json", "model.2017.valley.json", "model.2017.vdays.json",
            "model.2018.bls-summer.json", "model.2018.bls-winter.json", "model.2018.lover.json", "model.2018.spring.json"
        ]
    },
    {
        name: "33娘",
        path: "./model/33/",
        outfits: [
            "model.default.json", "model.2016.xmas.1.json", "model.2016.xmas.2.json",
            "model.2017.cba-normal.json", "model.2017.cba-super.json", "model.2017.newyear.json",
            "model.2017.school.json", "model.2017.summer.normal.1.json", "model.2017.summer.normal.2.json",
            "model.2017.summer.super.1.json", "model.2017.summer.super.2.json", "model.2017.tomo-bukatsu.high.json",
            "model.2017.tomo-bukatsu.low.json", "model.2017.valley.json", "model.2017.vdays.json",
            "model.2018.bls-summer.json", "model.2018.bls-winter.json", "model.2018.lover.json", "model.2018.spring.json"
        ]
    },
    { name: "康娜", path: "./model/Kobayaxi/", outfits: ["Kobayaxi.model.json"] },
    { name: "血小板", path: "./model/platelet/", outfits: ["model.json"] },
    { name: "纱雾", path: "./model/sagiri/", outfits: ["sagiri.model.json"] },
    { name: "小埋", path: "./model/xiaomai/", outfits: ["xiaomai.model.json"] }
];

const voiceListData = ["爱丽丝", "塔菲", "小孩姐", "才羽桃", "可莉", "丁真", "小团团", "曼波", "东雪莲"];

// --- 互动文本库 (新增) ---
const touchTexts = [
    "哎呀，别摸我啦！",
    "讨厌！",
    "哼~~",
    "再戳我就生气了哦！",
    "是在检查身体吗？",
    "哼，无聊...",
    "哇！吓我一跳！",
    "新年快乐呀！"
];

// --- 全局变量 ---
let selectedVoice = null;
let selectedImageBase64 = null;
let charIdx = 0;
let outfitIdx = 0;
let msgTimer = null;

let isDragging = false;
let isResizing = false;
let dragMoved = false;
let offset = { x: 0, y: 0 };

// 核心控制变量
let currentModel = null;
let audioContext = null;
let analyser = null;
let lipSyncInterval = null;
let hookInterval = null;

// **关键变量：全局口型数值**
// 音频分析器只修改这个值，具体的参数设置交给渲染循环
let globalLipSyncValue = 0;

let userId = localStorage.getItem('chat_user_id') || ('user_' + Math.random().toString(36).substr(2, 9));
localStorage.setItem('chat_user_id', userId);

// ==========================================
// 核心修复 1: 强力钩子 & 帧后覆盖
// ==========================================
function injectLive2DHook() {
    if (hookInterval) clearInterval(hookInterval);

    hookInterval = setInterval(() => {
        if (typeof window.Live2DModelWebGL !== 'undefined') {
            if (!window.Live2DModelWebGL.prototype._hooked) {
                const originalUpdate = window.Live2DModelWebGL.prototype.update;

                window.Live2DModelWebGL.prototype.update = function () {
                    // 1. 获取模型实例
                    currentModel = this;

                    // 2. 执行原有的更新逻辑 (包含物理、动作播放等)
                    // 如果不执行这个，模型就不动了
                    if (originalUpdate) originalUpdate.apply(this, arguments);

                    // 3. 【重点】在原有逻辑执行完之后，强制覆盖口型参数
                    // 这样就不会被模型自带的 idle 动作覆盖回去了
                    if (globalLipSyncValue > 0.01) {
                        // 兼容两种常见的参数命名
                        this.setParamFloat("PARAM_MOUTH_OPEN_Y", globalLipSyncValue);
                        this.setParamFloat("PARAM_MOUTH_OPEN", globalLipSyncValue);
                    }
                };

                window.Live2DModelWebGL.prototype._hooked = true;
                console.log("%c[Live2D Hook] 模型控制权与口型覆盖已激活！", "color: #42b983; font-weight: bold;");
                clearInterval(hookInterval);
            }
        }
    }, 100);
}

// ==========================================
// 加载模型 (高清设置)
// ==========================================
function loadModel() {
    const canvas = document.getElementById('live2d');

    // 强制高清分辨率
    canvas.width = 1500;
    canvas.height = 2500;

    const role = roleData[charIdx];
    const modelPath = role.path + (role.outfits[outfitIdx] || role.outfits[0]);

    if (window.loadlive2d) {
        currentModel = null;
        globalLipSyncValue = 0; // 重置口型
        injectLive2DHook(); // 确保 Hook 存在
        loadlive2d("live2d", modelPath);
        console.log(`[Model] Loaded: ${role.name}`);
    }
}

function showMsg(text) {
    const box = document.getElementById("message-box");
    box.innerHTML = text;
    box.style.pointerEvents = "none";
    box.classList.add("show");
    if (msgTimer) clearTimeout(msgTimer);
    msgTimer = setTimeout(() => box.classList.remove("show"), 5000);
}

// ==========================================
// 核心修复 2: 音频分析与全局变量更新
// ==========================================
function playVoiceWithLipSync(base64Audio) {
    if (!base64Audio) return;

    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!audioContext) audioContext = new AudioContext();
        if (audioContext.state === 'suspended') audioContext.resume();

        const audioData = atob(base64Audio);
        const arrayBuffer = new ArrayBuffer(audioData.length);
        const view = new Uint8Array(arrayBuffer);
        for (let i = 0; i < audioData.length; i++) view[i] = audioData.charCodeAt(i);

        audioContext.decodeAudioData(arrayBuffer, (buffer) => {
            const source = audioContext.createBufferSource();
            source.buffer = buffer;

            if (!analyser) analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;

            source.connect(analyser);
            analyser.connect(audioContext.destination);

            source.start(0);

            if (lipSyncInterval) clearInterval(lipSyncInterval);
            const dataArray = new Uint8Array(analyser.frequencyBinCount);

            // 启动定时器，只负责更新 globalLipSyncValue
            lipSyncInterval = setInterval(() => {
                analyser.getByteFrequencyData(dataArray);

                let sum = 0;
                // 取样前一半频率（人声主要区域）
                const binCount = Math.floor(dataArray.length / 2);
                for (let i = 0; i < binCount; i++) sum += dataArray[i];
                let volume = sum / binCount;

                // 增加灵敏度：只要有声音就尽量张大嘴
                let targetValue = 0;
                if (volume > 5) {
                    targetValue = (volume / 50); // 分母越小嘴巴张得越大
                }

                targetValue = Math.min(1.0, Math.max(0, targetValue));

                // 简单的平滑过渡，避免嘴巴抽搐
                globalLipSyncValue = globalLipSyncValue * 0.3 + targetValue * 0.7;

            }, 20); // 20ms 极速刷新

            source.onended = () => {
                clearInterval(lipSyncInterval);
                globalLipSyncValue = 0; // 播放结束强制闭嘴
            };

        }, (e) => console.error("音频解码失败", e));

    } catch (e) {
        console.error("语音播放系统错误:", e);
    }
}

async function fetchHistory() {
    const viewer = document.getElementById('history-viewer');
    viewer.innerHTML = '<div style="text-align:center;color:#999">载入中...</div>';
    try {
        const res = await fetch('/live2d_ai/get_history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ roleName: roleData[charIdx].name, userId: userId })
        });
        const data = await res.json();
        if (data.history && data.history.length > 0) {
            viewer.innerHTML = data.history.map(item => `
                <div style="margin-bottom:8px; padding-bottom:4px; border-bottom:1px solid #fff0f0; font-size:12px;">
                    <b style="color:#ff7675">${item.role === 'user' ? '我' : roleData[charIdx].name}:</b> 
                    <span style="color:#666">${item.content}</span>
                </div>
            `).join('');
            viewer.scrollTop = viewer.scrollHeight;
        } else {
            viewer.innerHTML = '<div style="text-align:center;color:#ccc">暂无往期回想</div>';
        }
    } catch (e) {
        viewer.innerHTML = '<div style="text-align:center;color:red">获取失败</div>';
    }
}

async function handleSend() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const text = input.value.trim();
    if (!text && !selectedImageBase64) return;

    sendBtn.disabled = true;
    showMsg(selectedImageBase64 ? "正在观察图片..." : "正在思考...");

    // 预激活 AudioContext (解决移动端/新版浏览器自动播放策略)
    if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
    if (audioContext.state === 'suspended') audioContext.resume();

    const currentMsg = text;
    const currentImg = selectedImageBase64;
    input.value = '';
    selectedImageBase64 = null;
    document.getElementById('image-preview-container').style.display = 'none';

    try {
        const res = await fetch('/live2d_ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: currentMsg,
                image: currentImg,
                roleName: roleData[charIdx].name,
                userId: userId,
                voice: selectedVoice
            })
        });
        const data = await res.json();
        showMsg(data.reply);

        if (data.audio) {
            playVoiceWithLipSync(data.audio);
        }

        if (document.getElementById('history-viewer').classList.contains('show')) fetchHistory();
    } catch (e) {
        console.error(e);
        showMsg("哎呀，连接 AI 失败了。");
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

// --- 初始化与事件绑定 ---

window.onload = () => {
    injectLive2DHook();

    const container = document.getElementById('resize-container');
    const widget = document.getElementById('live2d-widget');
    const voiceBox = document.getElementById('voice-box');
    const voiceListContainer = document.getElementById('voice-list-container');
    const aiBox = document.getElementById('ai-box');
    const imgInput = document.getElementById('image-input');
    const previewImg = document.getElementById('image-preview');
    const previewContainer = document.getElementById('image-preview-container');
    const canvas = document.getElementById('live2d');

    const savedW = localStorage.getItem('live2d-width') || 300;
    container.style.width = savedW + 'px';
    container.style.height = (savedW * 500 / 300) + 'px';
    loadModel();

    voiceListData.forEach(name => {
        const item = document.createElement('div');
        item.className = 'voice-item';
        item.innerText = name;
        item.onclick = () => {
            if (item.classList.contains('active')) {
                item.classList.remove('active');
                selectedVoice = null;
            } else {
                document.querySelectorAll('.voice-item').forEach(el => el.classList.remove('active'));
                item.classList.add('active');
                selectedVoice = name;
            }
        };
        voiceListContainer.appendChild(item);
    });

    document.getElementById('upload-btn').onclick = () => imgInput.click();
    imgInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 10 * 1024 * 1024) {
                showMsg("图片太大，请上传小于 10MB 的图片");
                imgInput.value = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const maxSize = 1024;
                    let width = img.width;
                    let height = img.height;
                    if (width > height) {
                        if (width > maxSize) { height *= maxSize / width; width = maxSize; }
                    } else {
                        if (height > maxSize) { width *= maxSize / height; height = maxSize; }
                    }
                    canvas.width = width;
                    canvas.height = height;
                    ctx.drawImage(img, 0, 0, width, height);
                    selectedImageBase64 = canvas.toDataURL('image/jpeg', 0.7);
                    previewImg.src = selectedImageBase64;
                    previewContainer.style.display = 'block';
                    showMsg("图片已压缩");
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    };
    document.getElementById('remove-img').onclick = () => {
        selectedImageBase64 = null;
        previewContainer.style.display = 'none';
        imgInput.value = '';
    };

    const startDrag = (e) => {
        isDragging = true;
        dragMoved = false;
        offset.x = e.clientX - widget.offsetLeft;
        offset.y = e.clientY - widget.offsetTop;
        e.preventDefault();
    };

    document.getElementById('drag-handle').onmousedown = startDrag;
    const restoreBtn = document.getElementById('restore-widget');
    restoreBtn.onmousedown = startDrag;

    restoreBtn.onclick = () => {
        if (!dragMoved) widget.classList.remove('minimized');
    };

    document.getElementById('resize-handle').onmousedown = (e) => {
        isResizing = true;
        e.preventDefault();
        e.stopPropagation();
    };

    // --- 视线跟随 ---
    document.onmousemove = (e) => {
        if (isDragging) {
            dragMoved = true;
            widget.style.left = (e.clientX - offset.x) + 'px';
            widget.style.top = (e.clientY - offset.y) + 'px';
            widget.style.bottom = 'auto';
            return;
        }
        if (isResizing) {
            let nw = e.clientX - widget.offsetLeft;
            if (nw > 150 && nw < 800) {
                container.style.width = nw + 'px';
                container.style.height = (nw * 500 / 300) + 'px';
            }
            return;
        }

        if (currentModel && !widget.classList.contains('minimized')) {
            const rect = canvas.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;

            let dx = (e.clientX - cx) / (rect.width / 2);
            let dy = -(e.clientY - cy) / (rect.height / 2);

            dx = Math.max(-1.5, Math.min(1.5, dx));
            dy = Math.max(-1.5, Math.min(1.5, dy));

            currentModel.setParamFloat("PARAM_ANGLE_X", dx * 30);
            currentModel.setParamFloat("PARAM_ANGLE_Y", dy * 30);
            currentModel.setParamFloat("PARAM_EYE_BALL_X", dx);
            currentModel.setParamFloat("PARAM_EYE_BALL_Y", dy);
            currentModel.setParamFloat("PARAM_BODY_ANGLE_X", dx * 10);
        }
    };

    document.onmouseup = () => {
        if (isResizing) {
            localStorage.setItem('live2d-width', container.offsetWidth);
        }
        isDragging = false;
        isResizing = false;
    };

    // --- 互动事件 (点击文本) ---
    canvas.onmousedown = (e) => {
        canvas.dataset.startX = e.clientX;
        canvas.dataset.startY = e.clientY;
    };

    canvas.onmouseup = (e) => {
        const startX = parseFloat(canvas.dataset.startX || 0);
        const startY = parseFloat(canvas.dataset.startY || 0);
        const dist = Math.sqrt(Math.pow(e.clientX - startX, 2) + Math.pow(e.clientY - startY, 2));

        if (dist < 10 && currentModel && !isDragging && !isResizing) {
            console.log("Interaction Triggered!");

            // 1. 随机动作
            const motions = ["tap_body", "pinch_out", "shake", "flick_head"];
            const randomMotion = motions[Math.floor(Math.random() * motions.length)];
            // 尝试播放动作，如果模型没有该动作组会自动忽略
            if (currentModel.startRandomMotion) {
                currentModel.startRandomMotion(randomMotion, 3);
            }

            // 2. 随机表情
            if (currentModel.setRandomExpression) {
                currentModel.setRandomExpression();
            }

            // 3. **核心修复：随机文本**
            const randomText = touchTexts[Math.floor(Math.random() * touchTexts.length)];
            showMsg(randomText);
        }
    };

    document.getElementById('close-widget').onclick = (e) => {
        e.stopPropagation();
        widget.classList.add('minimized');
    };

    document.getElementById('toggle-ai').onclick = () => {
        aiBox.classList.toggle('open');
        voiceBox.classList.remove('open');
    };
    document.getElementById('toggle-voice').onclick = () => {
        voiceBox.classList.toggle('open');
        aiBox.classList.remove('open');
    };

    document.getElementById('toggle-history').onclick = () => {
        const v = document.getElementById('history-viewer');
        v.classList.toggle('show');
        if (v.classList.contains('show')) fetchHistory();
    };

    document.getElementById('send-btn').onclick = handleSend;
    document.getElementById('chat-input').onkeypress = (e) => {
        if (e.key === 'Enter') handleSend();
    };

    document.getElementById('next-char-btn').onclick = () => {
        charIdx = (charIdx + 1) % roleData.length;
        outfitIdx = 0;
        loadModel();
        showMsg("你好，我是 " + roleData[charIdx].name);
    };
    document.getElementById('next-outfit-btn').onclick = () => {
        outfitIdx = (outfitIdx + 1) % roleData[charIdx].outfits.length;
        loadModel();
        showMsg("换好啦~");
    };

    // ==========================================
    // 语音转文字 (STT) 核心逻辑
    // ==========================================
    const sttBtn = document.getElementById('stt-btn');
    const chatInput = document.getElementById('chat-input');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.lang = 'zh-CN'; // 设置为中文识别
        recognition.interimResults = false; // 只显示最终结果
        let isListening = false;

        sttBtn.onclick = () => {
            // 确保在点击时激活 AudioContext
            if (audioContext && audioContext.state === 'suspended') audioContext.resume();

            if (!isListening) {
                try {
                    recognition.start();
                } catch (e) {
                    console.error("语音识别启动失败:", e);
                }
            } else {
                recognition.stop();
            }
        };

        recognition.onstart = () => {
            isListening = true;
            sttBtn.classList.add('recording'); // 触发 CSS 里的闪烁动画
            chatInput.placeholder = "正在听你说话...";
        };

        recognition.onresult = (event) => {
            const text = event.results[0][0].transcript;
            chatInput.value = text; // 将识别出的文字填入输入框
            showMsg("听到了：" + text);
        };

        recognition.onerror = (e) => {
            isListening = false;
            sttBtn.classList.remove('recording');
            if (e.error === 'not-allowed') {
                showMsg("权限不足，请在浏览器地址栏上方允许麦克风权限");
            } else {
                showMsg("语音识别出错了，请重试");
            }
        };

        recognition.onend = () => {
            isListening = false;
            sttBtn.classList.remove('recording');
            chatInput.placeholder = "和她说点什么...";
        };
    } else {
        // 如果浏览器不支持 (比如旧版 Firefox 或某些国产浏览器)
        sttBtn.onclick = () => showMsg("抱歉，您的浏览器不支持语音输入功能");
        sttBtn.style.opacity = "0.5";
    }
};