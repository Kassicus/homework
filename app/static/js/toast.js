/**
 * Toast Notification System
 * Provides floating notifications in the upper right corner
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = new Map();
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        this.container = document.querySelector('.toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', options = {}) {
        const defaults = {
            title: this.getDefaultTitle(type),
            duration: 5000,
            showProgress: true,
            closable: true,
            icon: this.getDefaultIcon(type)
        };

        const config = { ...defaults, ...options };
        const toastId = this.generateId();
        
        const toast = this.createToast(toastId, message, type, config);
        this.container.appendChild(toast);
        this.toasts.set(toastId, toast);

        // Trigger animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Auto dismiss
        if (config.duration > 0) {
            this.startProgressBar(toast, config.duration);
            setTimeout(() => {
                this.hide(toastId);
            }, config.duration);
        }

        return toastId;
    }

    createToast(id, message, type, config) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('data-toast-id', id);

        const header = document.createElement('div');
        header.className = 'toast-header';

        const titleContainer = document.createElement('div');
        titleContainer.style.display = 'flex';
        titleContainer.style.alignItems = 'center';

        if (config.icon) {
            const icon = document.createElement('i');
            icon.className = `bi ${config.icon} toast-icon`;
            titleContainer.appendChild(icon);
        }

        const title = document.createElement('h6');
        title.className = 'toast-title';
        title.textContent = config.title;
        titleContainer.appendChild(title);

        header.appendChild(titleContainer);

        if (config.closable) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'toast-close';
            closeBtn.innerHTML = '&times;';
            closeBtn.addEventListener('click', () => this.hide(id));
            header.appendChild(closeBtn);
        }

        const body = document.createElement('div');
        body.className = 'toast-body';
        body.textContent = message;

        toast.appendChild(header);
        toast.appendChild(body);

        if (config.showProgress && config.duration > 0) {
            const progress = document.createElement('div');
            progress.className = 'toast-progress';
            progress.style.width = '100%';
            toast.appendChild(progress);
        }

        return toast;
    }

    hide(toastId) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;

        toast.classList.add('hiding');
        toast.classList.remove('show');

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts.delete(toastId);
        }, 300);
    }

    startProgressBar(toast, duration) {
        const progress = toast.querySelector('.toast-progress');
        if (!progress) return;

        progress.style.transition = `width ${duration}ms linear`;
        setTimeout(() => {
            progress.style.width = '0%';
        }, 10);
    }

    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', options);
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    getDefaultTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };
        return titles[type] || 'Notification';
    }

    getDefaultIcon(type) {
        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-exclamation-triangle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };
        return icons[type] || 'bi-bell-fill';
    }

    generateId() {
        return 'toast-' + Math.random().toString(36).substr(2, 9);
    }

    clear() {
        this.toasts.forEach((toast, id) => {
            this.hide(id);
        });
    }
}

// Create global toast manager instance
window.Toast = new ToastManager();

// Helper functions for backward compatibility with Flask flash messages
window.showToast = (message, category = 'info') => {
    // Map Flask flash categories to toast types
    const typeMap = {
        'success': 'success',
        'error': 'error',
        'danger': 'error',
        'warning': 'warning',
        'info': 'info',
        'message': 'info'
    };
    
    const type = typeMap[category] || 'info';
    return window.Toast.show(message, type);
};

// Auto-show flash messages on page load
document.addEventListener('DOMContentLoaded', function() {
    // Look for flash messages in the page and convert them to toasts
    const flashMessages = document.querySelectorAll('[data-flash-message]');
    flashMessages.forEach(function(element) {
        const message = element.getAttribute('data-flash-message');
        const category = element.getAttribute('data-flash-category') || 'info';
        showToast(message, category);
        // Remove the element since we're showing it as a toast
        element.remove();
    });
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastManager;
}
