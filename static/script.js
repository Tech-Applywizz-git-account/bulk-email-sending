document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Toggle
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');

    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target) && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
            }
        }
    });

    // File Upload Drag & Drop
    const uploadZone = document.querySelector('.upload-zone');
    const fileInput = document.querySelector('.file-input');
    const fileInfo = document.getElementById('file-info');

    if (uploadZone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
        });

        uploadZone.addEventListener('drop', handleDrop, false);
        fileInput.addEventListener('change', handleFiles, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files; // Assign dropped files to input
            handleFiles();
        }

        function handleFiles() {
            const files = fileInput.files;
            if (files.length > 0) {
                const file = files[0];
                fileInfo.innerHTML = `
                    <div class="d-flex items-center gap-2" style="background: white; padding: 10px; border-radius: 8px; border: 1px solid var(--border-color); display: inline-flex; margin-top: 10px;">
                        <i class="fas fa-file-excel" style="color: #107c41;"></i>
                        <span style="font-weight: 500;">${file.name}</span>
                        <span class="text-sm text-muted">(${(file.size / 1024).toFixed(1)} KB)</span>
                    </div>
                `;
                // Auto submit optional? Or just show ready state.
                // For now, let user click "Upload" button or auto-submit if desired.
                const uploadBtnContainer = document.getElementById('upload-btn-container');
                if (uploadBtnContainer) {
                    uploadBtnContainer.style.display = 'block';
                }
            }

        }
    }

    // Table Filter / Search
    const searchInput = document.getElementById('table-search');
    if (searchInput) {
        searchInput.addEventListener('keyup', function () {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    } // End if searchInput

    // Select All Checkbox
    const selectAllBtn = document.getElementById('select-all');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('change', function () {
            const checkboxes = document.querySelectorAll('.row-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            toggleDeleteButton();
        });

        // Individual Checkbox change
        document.body.addEventListener('change', function (e) {
            if (e.target.classList.contains('row-checkbox')) {
                toggleDeleteButton();
                // Update Select All state
                const allCheckboxes = document.querySelectorAll('.row-checkbox');
                const allChecked = Array.from(allCheckboxes).every(cb => cb.checked);
                selectAllBtn.checked = allChecked;
            }
        });
    }

    function toggleDeleteButton() {
        const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
        const deleteBtn = document.getElementById('btn-delete-selected');
        if (deleteBtn) {
            deleteBtn.style.display = checkedBoxes.length > 0 ? 'inline-flex' : 'none';
        }
    }

    // Table Sorting
    const sortableHeaders = document.querySelectorAll('th.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const key = header.dataset.sort;
            const isAsc = !header.classList.contains('asc');

            // Reset others
            sortableHeaders.forEach(h => h.classList.remove('asc', 'desc'));
            header.classList.add(isAsc ? 'asc' : 'desc');
            const icon = header.querySelector('i');
            if (icon) {
                icon.className = isAsc ? 'fas fa-sort-up' : 'fas fa-sort-down';
            }

            rows.sort((a, b) => {
                const aVal = a.querySelector(`.col-${key}`).textContent.trim().toLowerCase();
                const bVal = b.querySelector(`.col-${key}`).textContent.trim().toLowerCase();

                if (aVal < bVal) return isAsc ? -1 : 1;
                if (aVal > bVal) return isAsc ? 1 : -1;
                return 0;
            });

            rows.forEach(row => tbody.appendChild(row));
        });
    });


    // Toast Notifications
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        // Auto remove after 5 seconds
        setTimeout(() => {
            removeToast(toast);
        }, 5000);

        // Close button
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => removeToast(toast));
        }
    });

    function removeToast(toast) {
        toast.style.opacity = '0';
        toast.addEventListener('transitionend', () => {
            toast.remove();
        });
    }
});

// Modal Functions (Global Scope)
function openAddModal() {
    const modal = document.getElementById('add-modal');
    if (modal) modal.style.display = 'flex';
}

function closeAddModal() {
    const modal = document.getElementById('add-modal');
    if (modal) modal.style.display = 'none';
}

function openEditModal(rowId, btn) {
    const row = btn.closest('tr');
    // Helper to allow for potential formatting differences
    const getText = (selector) => {
        const el = row.querySelector(selector);
        return el ? el.innerText.trim() : '';
    };

    const name = getText('.col-name');
    const email = getText('.col-email');
    const subject = getText('.col-subject');
    const body = getText('.col-body');

    const idInput = document.getElementById('edit-row-id');
    const nameInput = document.getElementById('edit-name');
    const emailInput = document.getElementById('edit-email');
    const subjectInput = document.getElementById('edit-subject');
    const bodyInput = document.getElementById('edit-body');

    if (idInput) idInput.value = rowId;
    if (nameInput) nameInput.value = name;
    if (emailInput) emailInput.value = email;
    if (subjectInput) subjectInput.value = subject;
    if (bodyInput) bodyInput.value = body;

    const modal = document.getElementById('edit-modal');
    if (modal) modal.style.display = 'flex';
}

function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    if (modal) modal.style.display = 'none';
}

function deleteSelectedRows(filename) {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    const indices = Array.from(checkedBoxes).map(cb => parseInt(cb.value));

    if (indices.length === 0) {
        alert("Please select at least one row to delete.");
        return;
    }

    if (!confirm(`Are you sure you want to delete ${indices.length} recipients?`)) return;

    fetch(`/files/${filename}/delete_rows`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ indices: indices })
    })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                response.text().then(text => alert('Failed to delete rows: ' + text));
            }
        })
        .catch(error => console.error('Error:', error));
}

// Close modals when clicking outside
window.onclick = function (event) {
    const addModal = document.getElementById('add-modal');
    const editModal = document.getElementById('edit-modal');
    if (event.target === addModal) {
        addModal.style.display = "none";
    }
    if (event.target === editModal) {
        editModal.style.display = "none";
    }
}




