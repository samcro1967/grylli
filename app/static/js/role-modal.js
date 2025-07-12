document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.change-role-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.getElementById('roleModalForm').action =
                roleChangeBase.replace("/0/", "/" + btn.dataset.userId + "/");
            document.getElementById('roleModalUserId').value = btn.dataset.userId;
            document.getElementById('roleModalUsername').textContent = btn.dataset.username;
            let value = btn.dataset.role;
            document.querySelectorAll('#roleModal input[type=radio][name=role]').forEach(function(radio) {
                radio.checked = (radio.value === value);
            });
            document.getElementById('roleModal').classList.remove('hidden');
        });
    });

    // Cancel button
    const cancelBtn = document.getElementById('roleModalCancel');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            document.getElementById('roleModal').classList.add('hidden');
        });
    }

    // Click-outside (defensive: check if modal exists)
    const roleModal = document.getElementById('roleModal');
    if (roleModal) {
        roleModal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
            }
        });
    }
});
