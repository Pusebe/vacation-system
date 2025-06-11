/**
 * JavaScript para admin en la página de festivos
 */

function approveHoliday(holidayId) {
    if (confirm('¿Aprobar este festivo trabajado?')) {
        fetch(`/holidays/${holidayId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Error al aprobar el festivo');
            }
        });
    }
}

function showEditHolidayModal(holidayId, date, description, status) {
    document.getElementById('editHolidayForm').action = `/holidays/${holidayId}/edit`;
    document.getElementById('editHolidayDate').value = date;
    document.getElementById('editHolidayDescription').value = description;
    document.getElementById('editHolidayStatus').value = status;
    new bootstrap.Modal(document.getElementById('editHolidayModal')).show();
}

function deleteHoliday(holidayId, userName, holidayDate) {
    if (confirm(`¿Eliminar el festivo trabajado de ${userName} del ${holidayDate}? Esta acción no se puede deshacer.`)) {
        fetch(`/holidays/${holidayId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Error al eliminar el festivo');
            }
        });
    }
}

function showRejectHolidayModal(holidayId, userName, holidayDate) {
    document.getElementById('rejectHolidayUserName').textContent = userName;
    document.getElementById('rejectHolidayDate').textContent = holidayDate;
    document.getElementById('rejectHolidayForm').action = `/holidays/${holidayId}/reject`;
    new bootstrap.Modal(document.getElementById('rejectHolidayModal')).show();
}

function toggleAdminCustomDescription() {
    const select = document.querySelector('#adminCreateHolidayModal select[name="description"]');
    const customDiv = document.getElementById('adminCustomDescriptionDiv');
    
    if (select.value === 'custom') {
        customDiv.classList.remove('d-none');
        customDiv.querySelector('input').required = true;
    } else {
        customDiv.classList.add('d-none');
        customDiv.querySelector('input').required = false;
    }
}

// Inicialización cuando se carga el DOM
document.addEventListener('DOMContentLoaded', function() {
    // Ajustar la descripción al enviar el formulario del admin
    const adminForm = document.querySelector('#adminCreateHolidayModal form');
    if (adminForm) {
        adminForm.addEventListener('submit', function(e) {
            const select = this.querySelector('select[name="description"]');
            const customInput = this.querySelector('input[name="custom_description"]');
            
            if (select.value === 'custom' && customInput.value.trim()) {
                // Crear un input hidden con la descripción personalizada
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'description';
                hiddenInput.value = customInput.value.trim();
                this.appendChild(hiddenInput);
                
                // Deshabilitar el select para que no envíe 'custom'
                select.disabled = true;
            }
        });
    }
});