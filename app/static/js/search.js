/**
 * Enhanced Universal Search Component JavaScript Functions
 */

// Global variables for search state
let searchTimeout;
let currentSearchQuery = '';
let searchSuggestions = [];
let searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');

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
    
    // Clear search results if on search page
    clearSearchResults();
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

// Live search suggestions
function fetchSearchSuggestions(query) {
    if (query.length < 2) {
        hideSearchSuggestions();
        return;
    }
    
    // Show loading state
    showSearchSuggestions([{ type: 'loading', text: 'Searching...' }]);
    
    // Fetch suggestions from backend
    fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.suggestions && data.suggestions.length > 0) {
                showSearchSuggestions(data.suggestions);
            } else {
                showSearchSuggestions([{ type: 'no-results', text: 'No suggestions found' }]);
            }
        })
        .catch(error => {
            console.error('Error fetching suggestions:', error);
            hideSearchSuggestions();
        });
}

// Show search suggestions dropdown
function showSearchSuggestions(suggestions) {
    let suggestionsContainer = document.getElementById('search-suggestions');
    if (!suggestionsContainer) {
        suggestionsContainer = document.createElement('div');
        suggestionsContainer.id = 'search-suggestions';
        suggestionsContainer.className = 'search-suggestions dropdown-menu show';
        suggestionsContainer.style.position = 'absolute';
        suggestionsContainer.style.top = '100%';
        suggestionsContainer.style.left = '0';
        suggestionsContainer.style.right = '0';
        suggestionsContainer.style.zIndex = '1000';
        suggestionsContainer.style.maxHeight = '300px';
        suggestionsContainer.style.overflowY = 'auto';
        
        const searchInput = document.querySelector('.search-form .form-control-lg');
        if (searchInput) {
            searchInput.parentNode.style.position = 'relative';
            searchInput.parentNode.appendChild(suggestionsContainer);
        }
    }
    
    // Build suggestions HTML
    let suggestionsHTML = '';
    suggestions.forEach(suggestion => {
        if (suggestion.type === 'loading') {
            suggestionsHTML += `
                <div class="dropdown-item text-muted">
                    <i class="bi bi-hourglass-split me-2"></i>${suggestion.text}
                </div>
            `;
        } else if (suggestion.type === 'no-results') {
            suggestionsHTML += `
                <div class="dropdown-item text-muted">
                    <i class="bi bi-info-circle me-2"></i>${suggestion.text}
                </div>
            `;
        } else {
            suggestionsHTML += `
                <div class="dropdown-item suggestion-item" data-suggestion="${suggestion.text}">
                    <i class="bi bi-search me-2"></i>${suggestion.text}
                    <small class="text-muted ms-2">${suggestion.category || ''}</small>
                </div>
            `;
        }
    });
    
    suggestionsContainer.innerHTML = suggestionsHTML;
    suggestionsContainer.style.display = 'block';
    
    // Add click handlers for suggestions
    const suggestionItems = suggestionsContainer.querySelectorAll('.suggestion-item');
    suggestionItems.forEach(item => {
        item.addEventListener('click', function() {
            const suggestion = this.dataset.suggestion;
            document.getElementById('search_query').value = suggestion;
            hideSearchSuggestions();
            performSearch(suggestion);
        });
    });
}

// Hide search suggestions
function hideSearchSuggestions() {
    const suggestionsContainer = document.getElementById('search-suggestions');
    if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }
}

// Perform search with AJAX
function performSearch(query) {
    if (!query || query.trim().length === 0) {
        return;
    }
    
    // Add to search history
    addToSearchHistory(query);
    
    // Show loading state
    showSearchLoading();
    
    // Get all form data
    const form = document.querySelector('.search-form');
    const formData = new FormData(form);
    
    // Build query string
    const params = new URLSearchParams();
    for (let [key, value] of formData.entries()) {
        if (value) {
            params.append(key, value);
        }
    }
    
    // Perform AJAX search
    fetch(`${form.action}?${params.toString()}`)
        .then(response => response.text())
        .then(html => {
            // Extract search results from HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Find and update existing page content instead of creating new containers
            updateExistingPageContent(doc, query);
            
            // Update search results summary
            updateSearchResultsSummary(query);
            
            // Hide loading state
            hideSearchLoading();
        })
        .catch(error => {
            console.error('Search error:', error);
            showMessage('Search failed. Please try again.', 'error');
            hideSearchLoading();
            
            // Show error in existing content area
            showSearchError();
        });
}

// Highlight search terms in results
function highlightSearchTerms(query) {
    if (!query || query.trim().length === 0) return;
    
    const terms = query.toLowerCase().split(' ').filter(term => term.length > 2);
    
    // Look for content in existing page areas
    const contentAreas = [
        '.table-responsive',
        '.search-results', 
        '.card-body',
        'tbody',
        '.contracts-list',
        '.clients-list'
    ];
    
    let highlighted = false;
    
    for (const selector of contentAreas) {
        const container = document.querySelector(selector);
        if (container) {
            // Highlight in text content
            const textNodes = container.querySelectorAll('td, p, span, div, h1, h2, h3, h4, h5, h6');
            textNodes.forEach(node => {
                if (node.children.length === 0) { // Only process text nodes
                    let text = node.textContent;
                    let nodeHighlighted = false;
                    
                    terms.forEach(term => {
                        const regex = new RegExp(`(${term})`, 'gi');
                        if (regex.test(text)) {
                            text = text.replace(regex, '<mark class="search-highlight">$1</mark>');
                            nodeHighlighted = true;
                            highlighted = true;
                        }
                    });
                    
                    if (nodeHighlighted) {
                        node.innerHTML = text;
                    }
                }
            });
            
            if (highlighted) break; // Stop after first successful highlighting
        }
    }
}

// Show search loading state
function showSearchLoading() {
    // Find existing content area to show loading state
    const existingContent = document.querySelector('.table-responsive, .search-results, .card-body, tbody');
    if (existingContent) {
        // Add loading class to existing content
        existingContent.classList.add('search-loading');
        
        // Show loading overlay
        const loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'search-loading-overlay';
        loadingOverlay.className = 'search-loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Searching...</span>
                </div>
                <p class="text-muted">Searching...</p>
            </div>
        `;
        
        // Position the overlay over the existing content
        existingContent.style.position = 'relative';
        existingContent.appendChild(loadingOverlay);
    }
}

// Hide search loading state
function hideSearchLoading() {
    // Remove loading class from existing content
    const existingContent = document.querySelector('.table-responsive, .search-results, .card-body, tbody');
    if (existingContent) {
        existingContent.classList.remove('search-loading');
    }
    
    // Remove loading overlay
    const loadingOverlay = document.getElementById('search-loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}



// Clear search results
function clearSearchResults() {
    // Reload the page to show all results
    window.location.reload();
}

// Update existing page content with search results
function updateExistingPageContent(doc, query) {
    // Look for existing content areas to update
    const existingAreas = [
        '.table-responsive',           // Main table area
        '.search-results',            // Search results area
        '.card-body',                 // Card body areas
        'tbody',                      // Table body
        '.contracts-list',            // Contracts list
        '.clients-list'               // Clients list
    ];
    
    let contentUpdated = false;
    
    for (const selector of existingAreas) {
        const existingContainer = document.querySelector(selector);
        const newContent = doc.querySelector(selector);
        
        if (existingContainer && newContent) {
            // Update the existing container with new content
            existingContainer.innerHTML = newContent.innerHTML;
            contentUpdated = true;
            
            // Highlight search terms in the updated content
            highlightSearchTerms(query);
            break;
        }
    }
    
    if (!contentUpdated) {
        // If no existing container found, try to find the main content area
        const mainContent = document.querySelector('main, .main-content, .container');
        if (mainContent) {
            // Look for the main results table or list
            const resultsTable = doc.querySelector('.table-responsive, tbody, .search-results');
            if (resultsTable) {
                // Find where to insert the results in the main content
                const existingTable = mainContent.querySelector('.table-responsive, tbody, .search-results');
                if (existingTable) {
                    existingTable.innerHTML = resultsTable.innerHTML;
                    highlightSearchTerms(query);
                    contentUpdated = true;
                }
            }
        }
    }
    
    // If still no content updated, show a message
    if (!contentUpdated) {
        showMessage('Search completed but could not update page content', 'warning');
    }
}

// Show search error in existing content
function showSearchError() {
    const mainContent = document.querySelector('.table-responsive, .search-results, .card-body');
    if (mainContent) {
        mainContent.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-exclamation-triangle fa-3x text-danger mb-3"></i>
                <h4 class="text-danger">Search Failed</h4>
                <p class="text-muted">Please try again or contact support if the problem persists.</p>
            </div>
        `;
    }
}

// Update search results summary
function updateSearchResultsSummary(query) {
    const summaryContainer = document.querySelector('.search-results-summary');
    if (summaryContainer) {
        // Count actual results in the page
        const resultCount = document.querySelectorAll('tbody tr, .contract-item, .client-item').length;
        if (resultCount > 0) {
            summaryContainer.querySelector('.text-muted').innerHTML = `
                <i class="bi bi-info-circle me-1"></i>
                Found ${resultCount} results for "${query}"
            `;
        } else {
            summaryContainer.querySelector('.text-muted').innerHTML = `
                <i class="bi bi-info-circle me-1"></i>
                No results found for "${query}"
            `;
        }
    }
}

// Add query to search history
function addToSearchHistory(query) {
    if (!query || query.trim().length === 0) return;
    
    // Remove if already exists
    searchHistory = searchHistory.filter(item => item !== query);
    
    // Add to beginning
    searchHistory.unshift(query);
    
    // Keep only last 10 searches
    if (searchHistory.length > 10) {
        searchHistory = searchHistory.slice(0, 10);
    }
    
    // Save to localStorage
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
}

// Show search history
function showSearchHistory() {
    if (searchHistory.length === 0) {
        showSearchSuggestions([{ type: 'no-results', text: 'No search history' }]);
        return;
    }
    
    const historySuggestions = searchHistory.map(query => ({
        type: 'history',
        text: query,
        category: 'Recent'
    }));
    
    showSearchSuggestions(historySuggestions);
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
            e.preventDefault();
            performSearch(e.target.value);
        }
        
        // Escape to hide suggestions
        if (e.key === 'Escape') {
            hideSearchSuggestions();
        }
        
        // Down arrow to navigate suggestions
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            navigateSuggestions('down');
        }
        
        // Up arrow to navigate suggestions
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            navigateSuggestions('up');
        }
    });
    
    // Add search input event listeners
    const searchInput = document.getElementById('search_query');
    if (searchInput) {
        // Live search suggestions
        searchInput.addEventListener('input', debounce(function() {
            const query = this.value.trim();
            currentSearchQuery = query;
            
            if (query.length >= 2) {
                fetchSearchSuggestions(query);
            } else {
                hideSearchSuggestions();
            }
        }, 300));
        
        // Focus events
        searchInput.addEventListener('focus', function() {
            if (this.value.trim().length >= 2) {
                fetchSearchSuggestions(this.value.trim());
            } else if (searchHistory.length > 0) {
                showSearchHistory();
            }
        });
        
        // Blur events
        searchInput.addEventListener('blur', function() {
            // Delay hiding to allow for clicks on suggestions
            setTimeout(hideSearchSuggestions, 200);
        });
        
        // Clear button functionality
        const clearButton = searchInput.parentNode.querySelector('.btn-clear');
        if (clearButton) {
            clearButton.addEventListener('click', function() {
                searchInput.value = '';
                hideSearchSuggestions();
                clearSearchResults();
                searchInput.focus();
            });
        }
    }
    
    // Add form submission handler
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('search_query').value.trim();
            if (query) {
                performSearch(query);
            }
        });
    }
}

// Navigate through search suggestions
function navigateSuggestions(direction) {
    const suggestionsContainer = document.getElementById('search-suggestions');
    if (!suggestionsContainer || suggestionsContainer.style.display === 'none') return;
    
    const items = suggestionsContainer.querySelectorAll('.suggestion-item');
    if (items.length === 0) return;
    
    const currentItem = suggestionsContainer.querySelector('.suggestion-item.active');
    let nextItem;
    
    if (!currentItem) {
        nextItem = direction === 'down' ? items[0] : items[items.length - 1];
    } else {
        const currentIndex = Array.from(items).indexOf(currentItem);
        if (direction === 'down') {
            nextItem = items[(currentIndex + 1) % items.length];
        } else {
            nextItem = items[currentIndex === 0 ? items.length - 1 : currentIndex - 1];
        }
    }
    
    // Remove active class from all items
    items.forEach(item => item.classList.remove('active'));
    
    // Add active class to next item
    nextItem.classList.add('active');
    
    // Scroll into view if needed
    nextItem.scrollIntoView({ block: 'nearest' });
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
window.performSearch = performSearch;
window.fetchSearchSuggestions = fetchSearchSuggestions;
window.clearSearchResults = clearSearchResults;
