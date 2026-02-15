const API_URL = "/api8000/api/messages";

// 管理模式状态
let isAdmin = false;

// 1. 加载留言
async function loadMsgs() {
    try {
        const res = await fetch(API_URL);
        const data = await res.json();
        const container = document.getElementById('msg-container');
        container.innerHTML = '';

        data.forEach(msg => {
            const div = document.createElement('div');
            div.className = 'message-item card';
            // 渲染留言，如果 isAdmin 为 true，则显示删除按钮
            // 注意：这里用到了 msg.id，必须依赖后端正确返回 id
            div.innerHTML = `
                <div class="msg-info">
                    <span class="msg-author">✨ ${msg.nickname}</span>
                    <span class="msg-time">${msg.time}</span>
                </div>
                <div class="msg-content">${msg.content}</div>
                ${isAdmin ? `<button class="del-btn" style="margin-top:10px; color:red; cursor:pointer;" onclick="deleteMsg(${msg.id})">删除</button>` : ''}
            `;
            container.appendChild(div);
        });
    } catch (err) {
        console.error("加载失败:", err);
    }
}

// 2. 提交留言
document.getElementById('submit-btn').onclick = async function () {
    const nickname = document.getElementById('nickname-input').value || "神秘旅客";
    const content = document.getElementById('msg-input').value;

    if (!content) return alert("内容不能为空");

    await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname, content })
    });

    document.getElementById('msg-input').value = '';
    loadMsgs(); // 刷新列表
};

// 3. 删除留言函数
// 必须挂载到 window 对象上，否则 HTML 中的 onclick 可能找不到它
window.deleteMsg = async function (id) {
    console.log("尝试删除ID:", id); // 调试用
    if (!id) {
        alert("错误：未获取到留言ID，请刷新页面重试");
        return;
    }

    const token = prompt("请输入管理密钥 (1230)：");
    if (!token) return;

    const res = await fetch(`${API_URL}/${id}?token=${token}`, {
        method: 'DELETE'
    });

    if (res.ok) {
        alert("删除成功！");
        loadMsgs();
    } else {
        alert("删除失败，密码错误或留言已不存在");
    }
};

// 4. 开启管理模式彩蛋 (点击标题5次)
let clickCount = 0;
const headerTitle = document.querySelector('.board-header h1');
if (headerTitle) {
    headerTitle.onclick = () => {
        clickCount++;
        if (clickCount >= 5) {
            isAdmin = !isAdmin;
            alert(isAdmin ? "已开启管理模式！(显示删除按钮)" : "管理模式已关闭");
            loadMsgs(); // 重新加载以显示或隐藏按钮
            clickCount = 0;
        }
    };
}

// 初始化加载
loadMsgs();