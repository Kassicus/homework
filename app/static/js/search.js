/**
 * Universal Search Component JavaScript Functions
 */

// Clear all advanced search filters
function clearAdvancedSearch() {
    // Clear date inputs
    document.getElementById('date_from').value = '';
    document.getElementById('date_to').value = '';
    
    // Reset select dropdowns to first option
    const selects = document.querySelectorAll('#advancedSearch select');
    selects.forEach(select => {
        select.selectedIndex = 0;
    });
    
    // Clear text inputs
    const textInputs = document.querySelectorAll('#advancedSearch input[type="text"]');
    textInputs.forEach(input => {
        input.value = '';
    });
    
    // Clear main search query
    const searchQuery = document.getElementById('search_query');
    if (searchQuery) {
        searchQuery.value = '';
    }
    
    // Show feedback
    showMessage('Filters cleared', 'info');
}

// Export search results
function exportResults() {
    const form = document.querySelector('.search-form');
    if (!form) {
        showMessage('Export form not found', 'error');
        return;
    }
    
    // Create a temporary form for export
    const exportForm = document.createElement('form');
    exportForm.method = 'POST';
    exportForm.action = form.action.replace('/search', '/export');
    
    // Copy all form data
    const formData = new FormData(form);
    for (let [key, value] of formData.entries()) {
        if (value) { // Only include non-empty values
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = value;
            exportForm.appendChild(input);
        }
    }
    
    // Add CSRF token if available
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    if (csrfToken) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = csrfToken.value;
        exportForm.appendChild(csrfInput);
    }
    
    // Submit the export form
    document.body.appendChild(exportForm);
    exportForm.submit();
    document.body.removeChild(exportForm);
    
    showMessage('Export started', 'success');
}

// Show message feedback
function showMessage(message, type = 'info') {
    // Check if there's already a message container
    let messageContainer = document.getElementById('search-message');
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.id = 'search-message';
        messageContainer.className = 'alert alert-dismissible fade show mt-3';
        messageContainer.style.position = 'fixed';
        messageContainer.style.top = '20px';
        messageContainer.style.right = '20px';
        messageContainer.style.zIndex = '9999';
        messageContainer.style.minWidth = '300px';
        
        // Insert after the search component
        const searchComponent = document.querySelector('.universal-search');
        if (searchComponent) {
            searchComponent.parentNode.insertBefore(messageContainer, searchComponent.nextSibling);
        } else {
            document.body.appendChild(messageContainer);
        }
    }
    
    // Set message content and styling
    const alertClass = `alert-${type === 'error' ? 'danger' : type}`;
    messageContainer.className = `alert ${alertClass} alert-dismissible fade show mt-3`;
    
    messageContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        if (messageContainer.parentNode) {
            messageContainer.remove();
        }
    }, 3000);
}

// Initialize search component
function initSearchComponent() {
    // Add event listeners for search type changes
    const searchType = document.getElementById('search_type');
    if (searchType) {
        searchType.addEventListener('change', function() {
            // You can add logic here to show/hide specific filters based on search type
            console.log('Search type changed to:', this.value);
        });
    }
    
    // Add event listeners for date inputs
    const dateFrom = document.getElementById('date_from');
    const dateTo = document.getElementById('date_to');
    
    if (dateFrom && dateTo) {
        // Ensure date_to is not before date_from
        dateFrom.addEventListener('change', function() {
            if (dateTo.value && this.value > dateTo.value) {
                dateTo.value = this.value;
            }
        });
        
        dateTo.addEventListener('change', function() {
            if (dateFrom.value && this.value < dateFrom.value) {
                dateFrom.value = this.value;
            }
        });
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('search_query');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Enter in search input to submit
        if (e.key === 'Enter' && e.target.id === 'search_query') {
            const form = e.target.closest('form');
            if (form) {
                form.submit();
            }
        }
    });
    
    // Add search suggestions (if available)
    const searchInput = document.getElementById('search_query');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            if (query.length >= 2) {
                // You can implement search suggestions here
                // fetchSearchSuggestions(query);
            }
        }, 300));
    }
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initSearchComponent();
});

// Export functions for global use
window.clearAdvancedSearch = clearAdvancedSearch;
window.exportResults = exportResults;
window.showMessage = showMessage;
