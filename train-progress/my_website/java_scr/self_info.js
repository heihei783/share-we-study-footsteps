// 1. 配置数据：图片路径、标题、描述
const photoData = [
    { src: '../img/瞬间/picture_01.jpg', title: '瞬间', desc: '光影总是最好的画笔' },
    { src: '../img/瞬间/picture_02.jpg', title: '流年', desc: '捕捉那一抹不经意的蓝' },
    { src: '../img/瞬间/picture_03.jpg', title: '角落', desc: '平凡生活里的微小诗意' },
    { src: '../img/瞬间/picture_04.jpg', title: '呼气', desc: '在云端寻找迷失的白昼' },
    { src: '../img/瞬间/picture_05.jpg', title: '重逢', desc: '每一个晚霞都是限定的温柔' },
    { src: '../img/瞬间/picture_06.jpg', title: '无声', desc: '让时间在快门声中慢下来' },
    { src: '../img/瞬间/picture_07.jpg', title: '归处', desc: '万物可爱，人间值得' }
];

let currentIndex = 0;
let timer = null;

const imgEl = document.getElementById('main-img');
const titleEl = document.getElementById('img-title');
const descEl = document.getElementById('img-desc');

// 2. 核心切换函数
function updateScene() {
    // 添加淡出类（需在CSS中定义 .fade-out { opacity: 0; }）
    imgEl.style.opacity = '0';

    setTimeout(() => {
        currentIndex = (currentIndex + 1) % photoData.length;
        const data = photoData[currentIndex];

        // 更新内容
        imgEl.src = data.src;
        titleEl.textContent = data.title;
        descEl.textContent = data.desc;

        // 图片加载后淡入
        imgEl.onload = () => {
            imgEl.style.opacity = '1';
        };
    }, 500); // 半秒渐变时间
}

// 3. 启动定时器（10000毫秒 = 10秒）
function startAutoPlay() {
    stopAutoPlay(); // 先清除旧的，防止重叠
    timer = setInterval(updateScene, 10000);
}

function stopAutoPlay() {
    if (timer) clearInterval(timer);
}

// 4. 初始化
startAutoPlay();

// 5. 进阶：点击图片立刻切换并重置计时
document.getElementById('auto-carousel').onclick = () => {
    updateScene();
    startAutoPlay(); // 重置 10 秒计时
};



const audio = document.getElementById('my-audio');
const musicBtn = document.getElementById('music-btn');

musicBtn.onclick = function () {
    if (audio.paused) {
        // 如果是暂停状态，则播放
        audio.play();
        musicBtn.classList.add('playing'); // 开启旋转
    } else {
        // 如果正在播放，则暂停
        audio.pause();
        musicBtn.classList.remove('playing'); // 停止旋转
    }
};

// 可选：如果音乐播完了（没有设置 loop 时），移除动画
audio.onended = function () {
    musicBtn.classList.remove('playing');
};