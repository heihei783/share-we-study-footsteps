document.querySelectorAll('.button a').forEach(link => {
    link.setAttribute('target', '_blank')
    link.setAttribute('rel', 'noopener')
})
const main_img_list = ['1', '2', '3', '4']
let curent_main_img = 0
const nextBtn = document.querySelector('#nextBtn')
nextBtn.onclick = function () {
    curent_main_img++
    if (curent_main_img >= main_img_list.length) {
        curent_main_img = 0
    }
    const main_img = main_img_list[curent_main_img]
    if (curent_main_img === 3)
        document.body.style.setProperty('--bj-url', `url('./img/main_img/main-${main_img}.png')`)
    else
        document.body.style.setProperty('--bj-url', `url('./img/main_img/main-${main_img}.jpg')`)

}


const listItems = document.querySelectorAll('.button ul li');

listItems.forEach(item => {
    item.style.cursor = 'pointer';

    item.addEventListener('click', function (e) {
        // 1. 获取当前按钮内部的 a 标签
        const link = item.querySelector('a');

        // 2. 如果没有链接，直接返回
        if (!link) return;

        // 3. 如果用户原本点击的就是文字(a标签)，浏览器会自动处理，我们不需要干涉
        // 否则会造成重复跳转或覆盖掉 target="_blank" 的新窗口属性
        if (e.target.closest('a')) return;

        // 4. 如果点击的是图片或背景，手动执行跳转
        const href = link.getAttribute('href');
        if (href && href !== '#' && href !== '#/') {
            // 检测是否需要新窗口打开（因为你前面的代码设置了 _blank）
            if (link.getAttribute('target') === '_blank') {
                window.open(href, '_blank');
            } else {
                window.location.href = href;
            }
        }
    });
});




// 获取所有处于“开发中”状态的容器
const devItems = document.querySelectorAll('.developing');

devItems.forEach(item => {
    // 统一处理点击事件（包括点击图片、文字或整个卡片）
    item.addEventListener('click', (e) => {
        // 阻止默认跳转行为（如果有的话）
        e.preventDefault();

        // 弹出温馨提示
        alert("✨ 敬请期待！");
    });
});


const canvas = document.getElementById('fireworks-canvas');
const ctx = canvas.getContext('2d');
let particles = [];

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();


class Particle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        // 1. 稍微随机的尺寸，增加层次感
        this.size = Math.random() * 3 + 1;

        const angle = Math.random() * Math.PI * 2;
        // 2. 强力的初始爆发
        const force = Math.random() * 8 + 4;
        this.speedX = Math.cos(angle) * force;
        this.speedY = Math.sin(angle) * force;

        this.gravity = 0.12; // 3. 较低重力，让粒子飘得更久
        this.friction = 0.96; // 4. 适中的摩擦力

        // 5. 鲜艳的颜色池
        const colors = ['#00E5FF', '#FF0050', '#FFD600', '#00FF41', '#FF3D00', '#FFFFFF'];
        this.color = colors[Math.floor(Math.random() * colors.length)];
        this.opacity = 1;
    }

    update() {
        this.speedX *= this.friction;
        this.speedY *= this.friction;
        this.speedY += this.gravity;
        this.x += this.speedX;
        this.y += this.speedY;
        // 6. 减慢消失速度：从 0.08 改为 0.018，停留时间变长
        this.opacity -= 0.018;
    }

    draw() {
        if (this.opacity <= 0) return;
        ctx.globalAlpha = this.opacity;
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

// 核心修复点：将点击坐标传给生成函数
function createParticles(e) {
    // 每次点击生成 45 个粒子
    for (let i = 0; i < 45; i++) {
        particles.push(new Particle(e.clientX, e.clientY));
    }
}

// 7. 重要！必须添加这个监听器，否则点击无反应
window.addEventListener('mousedown', createParticles);

function animate() {
    // 8. 彻底清理画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();
        if (particles[i].opacity <= 0) {
            particles.splice(i, 1);
            i--;
        }
    }
    requestAnimationFrame(animate);
}
animate();



//------------------------------红包----------------------------

// 页面加载 1.2 秒后自动弹出红包
window.addEventListener('load', () => {
    setTimeout(() => {
        const popup = document.getElementById('red-envelope-popup');
        if (popup) popup.classList.add('show');
    }, 1200);
});

// 关闭红包函数
function closeRedPopup() {
    const popup = document.getElementById('red-envelope-popup');
    if (popup) {
        popup.style.top = '-150px'; // 向上缩回
        popup.style.opacity = '0';
    }
}

//-----------------------------------------------------------


