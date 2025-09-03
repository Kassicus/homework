/**
 * Contract Management Platform - Main JavaScript
 * Handles AJAX functionality, form interactions, and dynamic content updates
 */

$(document).ready(function() {
    'use strict';
    
    // Initialize tooltips and popovers
    $('[data-bs-toggle="tooltip"]').tooltip();
    $('[data-bs-toggle="popover"]').popover();
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize clear buttons
    initializeClearButtons();
    
    // Initialize form handling
    initializeForms();
    
    // Initialize AJAX loading states
    initializeLoadingStates();
});

/**
 * Initialize search functionality with AJAX
 */
function initializeSearch() {
    // Contract search form
    $('#contract-search-form').on('submit', function(e) {
        e.preventDefault();
        performContractSearch();
    });
    
    // Client search form
    $('#client-search-form').on('submit', function(e) {
        e.preventDefault();
        performClientSearch();
    });
    
    // Real-time search input
    $('#search-query').on('input', debounce(function() {
        if ($(this).val().length >= 2) {
            performLiveSearch($(this).val());
        }
    }, 300));
}

/**
 * Perform contract search via AJAX
 */
function performContractSearch() {
    const form = $('#contract-search-form');
    const resultsContainer = $('#search-results');
    const loadingSpinner = $('#search-loading');
    
    // Show loading state
    form.addClass('loading');
    loadingSpinner.show();
    resultsContainer.hide();
    
    $.ajax({
        url: form.attr('action'),
        method: 'POST',
        data: form.serialize(),
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                displaySearchResults(response.results, resultsContainer);
            } else {
                showErrorMessage('Search failed: ' + response.message);
            }
        },
        error: function(xhr, status, error) {
            showErrorMessage('Search error: ' + error);
        },
        complete: function() {
            form.removeClass('loading');
            loadingSpinner.hide();
            resultsContainer.show();
        }
    });
}

/**
 * Perform client search via AJAX
 */
function performClientSearch() {
    const form = $('#client-search-form');
    const resultsContainer = $('#client-search-results');
    const loadingSpinner = $('#client-search-loading');
    
    // Show loading state
    form.addClass('loading');
    loadingSpinner.show();
    resultsContainer.hide();
    
    $.ajax({
        url: form.attr('action'),
        method: 'POST',
        data: form.serialize(),
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                displayClientSearchResults(response.results, resultsContainer);
            } else {
                showErrorMessage('Client search failed: ' + response.message);
            }
        },
        error: function(xhr, status, error) {
            showErrorMessage('Client search error: ' + error);
        },
        complete: function() {
            form.removeClass('loading');
            loadingSpinner.hide();
            resultsContainer.show();
        }
    });
}

/**
 * Perform live search as user types
 */
function performLiveSearch(query) {
    $.ajax({
        url: '/api/search/live',
        method: 'GET',
        data: { q: query },
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                displayLiveSearchResults(response.results);
            }
        },
        error: function(xhr, status, error) {
            console.error('Live search error:', error);
        }
    });
}

/**
 * Display search results in the container
 */
function displaySearchResults(results, container) {
    if (!results || results.length === 0) {
        container.html('<div class="text-center py-4"><p class="text-muted">No contracts found matching your search criteria.</p></div>');
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-hover">';
    html += '<thead><tr><th>Title</th><th>Client</th><th>Status</th><th>Type</th><th>Created</th><th>Actions</th></tr></thead><tbody>';
    
    results.forEach(function(contract) {
        html += '<tr>';
        html += '<td><strong>' + escapeHtml(contract.title) + '</strong></td>';
        html += '<td>' + escapeHtml(contract.client_name || 'N/A') + '</td>';
        html += '<td><span class="badge bg-' + getStatusBadgeClass(contract.status) + '">' + contract.status + '</span></td>';
        html += '<td>' + escapeHtml(contract.contract_type || 'N/A') + '</td>';
        html += '<td>' + (contract.created_date || 'N/A') + '</td>';
        html += '<td><a href="/contracts/' + contract.id + '" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i></a></td>';
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.html(html);
}

/**
 * Display client search results
 */
function displayClientSearchResults(results, container) {
    if (!results || results.length === 0) {
        container.html('<div class="text-center py-4"><p class="text-muted">No clients found matching your search criteria.</p></div>');
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-hover">';
    html += '<thead><tr><th>Name</th><th>Organization</th><th>Email</th><th>Phone</th><th>Actions</th></tr></thead><tbody>';
    
    results.forEach(function(client) {
        html += '<tr>';
        html += '<td><strong>' + escapeHtml(client.name) + '</strong></td>';
        html += '<td>' + escapeHtml(client.organization || 'N/A') + '</td>';
        html += '<td>' + escapeHtml(client.email || 'N/A') + '</td>';
        html += '<td>' + escapeHtml(client.phone || 'N/A') + '</td>';
        html += '<td><a href="/clients/' + client.id + '" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i></a></td>';
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.html(html);
}

/**
 * Display live search results in dropdown
 */
function displayLiveSearchResults(results) {
    const dropdown = $('#live-search-dropdown');
    
    if (!results || results.length === 0) {
        dropdown.hide();
        return;
    }
    
    let html = '';
    results.slice(0, 5).forEach(function(result) {
        html += '<a class="dropdown-item" href="/contracts/' + result.id + '">';
        html += '<div><strong>' + escapeHtml(result.title) + '</strong></div>';
        html += '<small class="text-muted">' + escapeHtml(result.client_name || 'N/A') + ' • ' + result.status + '</small>';
        html += '</a>';
    });
    
    dropdown.html(html).show();
}

/**
 * Initialize form handling
 */
function initializeForms() {
    // Auto-save forms
    $('.auto-save-form').on('change', debounce(function() {
        autoSaveForm($(this));
    }, 1000));
    
    // File upload preview
    $('.file-upload').on('change', function() {
        previewFileUpload(this);
    });
    
    // Form validation
    $('.needs-validation').on('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
}

/**
 * Auto-save form data
 */
function autoSaveForm(form) {
    const formData = new FormData(form[0]);
    const saveIndicator = form.find('.save-indicator');
    
    saveIndicator.html('<i class="bi bi-arrow-clockwise spinner-border-sm"></i> Saving...');
    
    $.ajax({
        url: form.attr('action') + '/autosave',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                saveIndicator.html('<i class="bi bi-check-circle text-success"></i> Saved');
                setTimeout(function() {
                    saveIndicator.html('');
                }, 2000);
            }
        },
        error: function() {
            saveIndicator.html('<i class="bi bi-exclamation-triangle text-danger"></i> Save failed');
        }
    });
}

/**
 * Preview file upload
 */
function previewFileUpload(input) {
    const preview = $(input).siblings('.file-preview');
    const file = input.files[0];
    
    if (file) {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.html('<img src="' + e.target.result + '" class="img-thumbnail" style="max-height: 100px;">');
            };
            reader.readAsDataURL(file);
        } else {
            preview.html('<div class="text-muted"><i class="bi bi-file-earmark"></i> ' + file.name + '</div>');
        }
    } else {
        preview.html('');
    }
}

/**
 * Initialize loading states
 */
function initializeLoadingStates() {
    // Button loading states
    $('.btn-loading').on('click', function() {
        const btn = $(this);
        const originalText = btn.text();
        
        btn.prop('disabled', true)
           .html('<span class="spinner-border spinner-border-sm me-2"></span>Loading...');
        
        // Re-enable after 5 seconds as fallback
        setTimeout(function() {
            btn.prop('disabled', false).text(originalText);
        }, 5000);
    });
    
    // Form loading states
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        if (submitBtn.length && !submitBtn.hasClass('btn-loading')) {
            submitBtn.prop('disabled', true).text('Processing...');
        }
    });
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    const alertHtml = '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
                     message +
                     '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>';
    
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert-danger').fadeOut('slow');
    }, 5000);
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    const alertHtml = '<div class="alert alert-success alert-dismissible fade show" role="alert">' +
                     message +
                     '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>';
    
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-hide after 3 seconds
    setTimeout(function() {
        $('.alert-success').fadeOut('slow');
    }, 3000);
}

/**
 * Utility function to escape HTML
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * Utility function to debounce function calls
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Get status badge class
 */
function getStatusBadgeClass(status) {
    const statusMap = {
        'draft': 'secondary',
        'under_review': 'warning',
        'active': 'success',
        'expired': 'danger',
        'terminated': 'dark',
        'renewed': 'info'
    };
    return statusMap[status] || 'secondary';
}

/**
 * Export search results
 */
function exportSearchResults(format) {
    const form = $('#contract-search-form');
    const formData = new FormData(form[0]);
    formData.append('export_format', format);
    
    // Create temporary form for download
    const tempForm = $('<form>', {
        method: 'POST',
        action: '/contracts/export',
        target: '_blank'
    });
    
    for (let [key, value] of formData.entries()) {
        tempForm.append($('<input>', {
            type: 'hidden',
            name: key,
            value: value
        }));
    }
    
    $('body').append(tempForm);
    tempForm.submit();
    tempForm.remove();
}

/**
 * Initialize clear button functionality
 */
function initializeClearButtons() {
    // Clear search input button
    $('.btn-clear').on('click', function() {
        const searchInput = $(this).siblings('input[name="q"]');
        searchInput.val('');
        
        // Submit the form to clear the search
        $(this).closest('form').submit();
    });
}

/**
 * Clear advanced search filters
 */
function clearAdvancedSearch() {
    // Clear all form inputs in the advanced search section
    const advancedSearchForm = document.querySelector('.search-form');
    if (advancedSearchForm) {
        // Clear all input fields except the main search query
        const inputs = advancedSearchForm.querySelectorAll('input:not([name="q"]), select');
        inputs.forEach(input => {
            if (input.type === 'date' || input.type === 'text') {
                input.value = '';
            } else if (input.tagName === 'SELECT') {
                input.selectedIndex = 0;
            }
        });
        
        // Submit the form to apply the cleared filters
        advancedSearchForm.submit();
    }
}

/**
 * Export results function (placeholder)
 */
function exportResults() {
    // This function can be implemented later for exporting filtered results
    console.log('Export functionality not yet implemented');
}
