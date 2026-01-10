// Enhanced clipboard functionality
class ClipboardManager {
    constructor() {
        this.initClipboardButtons();
        this.setupGlobalListeners();
    }
    
    initClipboardButtons() {
        // Find all copy buttons and attach handlers
        document.querySelectorAll('[data-copy-text]').forEach(button => {
            button.addEventListener('click', (e) => {
                this.copyToClipboard(e.target);
            });
        });
    }
    
    setupGlobalListeners() {
        // Listen for dynamically added copy buttons
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length) {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1) { // Element node
                            if (node.hasAttribute('data-copy-text')) {
                                node.addEventListener('click', (e) => {
                                    this.copyToClipboard(e.target);
                                });
                            }
                            // Check child elements
                            node.querySelectorAll('[data-copy-text]').forEach(button => {
                                button.addEventListener('click', (e) => {
                                    this.copyToClipboard(e.target);
                                });
                            });
                        }
                    });
                }
            });
        });
        
        // Start observing the document body for changes
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    copyToClipboard(button) {
        const text = button.getAttribute('data-copy-text');
        const originalText = button.innerHTML;
        const originalClasses = button.className;
        const originalStyles = button.style.cssText;
        
        // Use modern clipboard API
        navigator.clipboard.writeText(text).then(() => {
            // Success feedback
            button.innerHTML = '✅ Copied!';
            button.style.backgroundColor = '#28a745';
            button.style.color = 'white';
            button.style.borderColor = '#218838';
            
            // Show toast notification
            this.showToast('Summary copied to clipboard!', 'success');
            
            // Reset after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalText;
                button.className = originalClasses;
                button.style.cssText = originalStyles;
            }, 2000);
            
        }).catch(err => {
            console.error('Copy failed:', err);
            
            // Try fallback method
            if (this.fallbackCopyToClipboard(text)) {
                button.innerHTML = '✅ Copied!';
                button.style.backgroundColor = '#28a745';
                button.style.color = 'white';
                
                this.showToast('Summary copied to clipboard!', 'success');
            } else {
                button.innerHTML = '❌ Failed';
                button.style.backgroundColor = '#dc3545';
                button.style.color = 'white';
                
                this.showToast('Failed to copy. Please try again.', 'error');
            }
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.className = originalClasses;
                button.style.cssText = originalStyles;
            }, 2000);
        });
    }
    
    // Fallback for older browsers
    fallbackCopyToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            return successful;
        } catch (err) {
            console.error('Fallback copy failed:', err);
            document.body.removeChild(textArea);
            return false;
        }
    }
    
    showToast(message, type = 'success') {
        // Remove existing toast
        const existingToast = document.querySelector('.clipboard-toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `clipboard-toast clipboard-toast-${type}`;
        toast.innerHTML = message;
        
        // Style the toast
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : '#dc3545'};
            color: white;
            padding: 12px 24px;
            border-radius: 5px;
            z-index: 10000;
            animation: toastFade 2s forwards;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 500;
        `;
        
        // Add animation styles if not already present
        if (!document.querySelector('#toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                @keyframes toastFade {
                    0% { opacity: 0; transform: translateY(-20px) translateX(20px); }
                    10% { opacity: 1; transform: translateY(0) translateX(0); }
                    90% { opacity: 1; transform: translateY(0) translateX(0); }
                    100% { opacity: 0; transform: translateY(-20px) translateX(20px); }
                }
                
                .clipboard-toast {
                    pointer-events: none;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(toast);
        
        // Remove toast after animation
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 2000);
    }
    
    // Public method to copy text programmatically
    copyText(text, successCallback = null, errorCallback = null) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text)
                .then(() => {
                    if (successCallback) successCallback();
                    this.showToast('Text copied to clipboard!', 'success');
                })
                .catch(err => {
                    console.error('Copy failed:', err);
                    if (errorCallback) errorCallback(err);
                    this.showToast('Failed to copy text.', 'error');
                });
        } else {
            // Use fallback
            if (this.fallbackCopyToClipboard(text)) {
                if (successCallback) successCallback();
                this.showToast('Text copied to clipboard!', 'success');
            } else {
                if (errorCallback) errorCallback(new Error('Fallback copy failed'));
                this.showToast('Failed to copy text.', 'error');
            }
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.clipboardManager = new ClipboardManager();
    
    // Expose copyText as a global function
    window.copyToClipboard = (text, elementId = null) => {
        if (elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                window.clipboardManager.copyToClipboard(element);
                return;
            }
        }
        window.clipboardManager.copyText(text);
    };
    
    // Add CSS for copy buttons if not already present
    if (!document.querySelector('#clipboard-styles')) {
        const style = document.createElement('style');
        style.id = 'clipboard-styles';
        style.textContent = `
            [data-copy-text] {
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            [data-copy-text]:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            [data-copy-text]:active {
                transform: translateY(0);
            }
            
            .copy-btn-success {
                background-color: #28a745 !important;
                color: white !important;
                border-color: #218838 !important;
            }
            
            .copy-btn-error {
                background-color: #dc3545 !important;
                color: white !important;
                border-color: #c82333 !important;
            }
        `;
        document.head.appendChild(style);
    }
});

// Export for module usage (if using ES6 modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClipboardManager;
}