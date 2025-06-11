// Sistema de notificaciones moderno y robusto
let notificationPolling;
let lastUpdateTime = new Date();

document.addEventListener('DOMContentLoaded', function() {
    initializeNotificationSystem();
    setupAlertDismiss();
});

function initializeNotificationSystem() {
    updateNotificationBadge();
    notificationPolling = setInterval(() => {
        updateNotificationBadge();
        updateLastUpdateDisplay();
    }, 30000);
}

async function updateNotificationBadge() {
    try {
        const response = await fetch('/api/notifications');
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        const badge = document.getElementById('notification-badge');
        
        if (badge) {
            if (data.count > 0) {
                badge.textContent = data.count > 99 ? '99+' : data.count;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }
        
        lastUpdateTime = new Date();
    } catch (error) {
        console.error('Error updating notification badge:', error);
    }
}

async function loadNotificationsList() {
    const container = document.getElementById('notifications-container');
    if (!container) return;
    
    // Mostrar estado de carga
    container.innerHTML = `
        <div class="notification-loading">
            <div class="spinner-border spinner-border-sm text-primary me-2"></div>
            <span>Cargando notificaciones...</span>
        </div>
    `;
    
    try {
        const response = await fetch('/api/notifications/list');
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        renderNotifications(data.notifications);
        lastUpdateTime = new Date();
        updateLastUpdateDisplay();
        
    } catch (error) {
        console.error('Error loading notifications:', error);
        container.innerHTML = `
            <div class="notification-error">
                <i class="ti ti-wifi-off text-danger fs-2 mb-3"></i>
                <div class="fw-bold mb-2">Error de conexión</div>
                <div class="mb-3">No se pudieron cargar las notificaciones</div>
                <button class="btn btn-sm btn-outline-primary" onclick="loadNotificationsList()">
                    <i class="ti ti-refresh me-1"></i>Reintentar
                </button>
            </div>
        `;
    }
}

function renderNotifications(notifications) {
    const container = document.getElementById('notifications-container');
    
    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="notification-empty">
                <i class="ti ti-bell-off notification-empty-icon"></i>
                <div class="fw-medium mb-2">Todo al día</div>
                <div>No tienes notificaciones pendientes</div>
            </div>
        `;
        return;
    }
    
    const html = notifications.map(notification => 
        renderNotificationItem(notification)
    ).join('');
    
    container.innerHTML = html;
}

function renderNotificationItem(notification) {
    const isUnread = !notification.is_read;
    const avatarClass = getNotificationAvatarClass(notification.type);
    
    return `
        <div class="notification-item ${isUnread ? 'unread' : ''}" 
             onclick="markNotificationRead(${notification.id})"
             data-notification-id="${notification.id}">
            <div class="d-flex align-items-start">
                <div class="notification-avatar ${avatarClass}">
                    <i class="ti ti-${notification.icon}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title-text">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">
                        <i class="ti ti-clock me-1"></i>
                        ${formatTime(notification.created_at)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function markNotificationRead(id) {
    const item = document.querySelector(`[data-notification-id="${id}"]`);
    if (!item || !item.classList.contains('unread')) return;
    
    // Feedback visual inmediato
    item.style.opacity = '0.7';
    item.classList.remove('unread');
    
    try {
        const response = await fetch(`/api/notifications/${id}/read`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            updateNotificationBadge();
        } else {
            // Revertir si hay error
            item.style.opacity = '1';
            item.classList.add('unread');
        }
    } catch (error) {
        console.error('Error marking notification as read:', error);
        // Revertir si hay error
        item.style.opacity = '1';
        item.classList.add('unread');
    }
}

async function markAllAsRead() {
    const btn = document.getElementById('markAllBtn');
    const originalContent = btn.innerHTML;
    
    // Feedback visual
    btn.innerHTML = '<i class="ti ti-loader"></i>';
    btn.disabled = true;
    btn.style.opacity = '0.7';
    
    try {
        const response = await fetch('/api/notifications/mark-all-read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            // Actualizar todas las notificaciones visualmente
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
                item.style.opacity = '0.7';
            });
            
            updateNotificationBadge();
            
            // Feedback de éxito
            btn.innerHTML = '<i class="ti ti-check"></i>';
            btn.style.background = 'var(--tblr-success-lt)';
            btn.style.color = 'var(--tblr-success)';
            
            setTimeout(() => {
                btn.innerHTML = originalContent;
                btn.style.background = '';
                btn.style.color = '';
                btn.style.opacity = '';
                btn.disabled = false;
            }, 1500);
        } else {
            throw new Error('Failed to mark all as read');
        }
    } catch (error) {
        console.error('Error marking all as read:', error);
        btn.innerHTML = originalContent;
        btn.style.opacity = '';
        btn.disabled = false;
    }
}

function refreshNotifications() {
    const btn = event.target.closest('button');
    const originalContent = btn.innerHTML;
    
    btn.innerHTML = '<i class="ti ti-loader"></i>';
    btn.disabled = true;
    
    Promise.all([
        loadNotificationsList(),
        updateNotificationBadge()
    ]).finally(() => {
        setTimeout(() => {
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }, 500);
    });
}

function getNotificationAvatarClass(type) {
    const classes = {
        'request_pending': 'notification-type-warning',
        'request_approved': 'notification-type-success',
        'request_rejected': 'notification-type-danger',
        'holiday_pending': 'notification-type-info',
        'holiday_approved': 'notification-type-success',
        'vacation_reminder': 'notification-type-primary',
        'system': 'notification-type-info'
    };
    return classes[type] || 'notification-type-primary';
}

function formatTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMinutes < 1) return 'Ahora mismo';
    if (diffMinutes < 60) return `hace ${diffMinutes}m`;
    if (diffHours < 24) return `hace ${diffHours}h`;
    if (diffDays < 7) return `hace ${diffDays}d`;
    if (diffDays < 30) return `hace ${Math.floor(diffDays / 7)}sem`;
    
    return date.toLocaleDateString('es-ES', {
        day: 'numeric',
        month: 'short'
    });
}

function updateLastUpdateDisplay() {
    const element = document.getElementById('last-update');
    if (element) {
        element.textContent = formatTime(lastUpdateTime.toISOString());
    }
}

function setupAlertDismiss() {
    setTimeout(() => {
        document.querySelectorAll('.alert-dismissible .btn-close').forEach(btn => {
            if (btn) btn.click();
        });
    }, 5000);
}

// Cleanup al salir
window.addEventListener('beforeunload', () => {
    if (notificationPolling) {
        clearInterval(notificationPolling);
    }
});