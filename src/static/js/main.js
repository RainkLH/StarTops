/* Startops 前端主程序 */

/**
 * 页面导航函数
 * @param {string} url - 要加载的页面URL
 * @param {Event} event - 点击事件对象
 */
function showPage(url, event) {
    if (event) {
        event.preventDefault();
    }
    
    // 更新活动菜单项
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
    
    // 加载页面到iframe
    const frame = document.getElementById('content-frame');
    if (frame) {
        frame.src = url;
    }
}

/**
 * 更新时间戳
 */
function updateTimestamp() {
    const timestamp = document.getElementById('timestamp');
    if (timestamp) {
        const now = new Date();
        timestamp.textContent = now.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

/**
 * 获取API数据
 */
async function apiGet(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (response.ok) {
            return await response.json();
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    } catch (error) {
        console.error('API error:', error);
        return null;
    }
}

/**
 * 发送API请求
 */
async function apiPost(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            return await response.json();
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    } catch (error) {
        console.error('API error:', error);
        return null;
    }
}

/**
 * 显示通知
 */
function showNotification(type, message, duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${
            type === 'success' ? '#d4edda' :
            type === 'error' ? '#f8d7da' :
            type === 'warning' ? '#fff3cd' :
            '#d1ecf1'
        };
        color: ${
            type === 'success' ? '#155724' :
            type === 'error' ? '#721c24' :
            type === 'warning' ? '#856404' :
            '#0c5460'
        };
        border: 1px solid ${
            type === 'success' ? '#c3e6cb' :
            type === 'error' ? '#f5c6cb' :
            type === 'warning' ? '#ffeaa7' :
            '#bee5eb'
        };
        border-radius: 4px;
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    if (duration > 0) {
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}

/**
 * 初始化页面
 */
document.addEventListener('DOMContentLoaded', () => {
    // 更新时间戳
    updateTimestamp();
    setInterval(updateTimestamp, 1000);
    
    // 绑定导航链接
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href && href !== '#') {
                e.preventDefault();
                showPage(href);
            }
        });
    });
});

// 添加样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(400px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(400px);
        }
    }
`;
document.head.appendChild(style);
