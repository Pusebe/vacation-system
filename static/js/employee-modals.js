// static/js/employee-modals.js - Manejo de modales para empleados (solo funciones)

document.addEventListener('DOMContentLoaded', function() {
    initializeEmployeeModals();
});

function initializeEmployeeModals() {
    console.log('Inicializando modales de empleado...');
    
    // Modal de vacaciones (newRequestModal)
    const vacationModal = document.getElementById('newRequestModal');
    if (vacationModal) {
        vacationModal.addEventListener('hidden.bs.modal', function() {
            clearDatePickers('newRequestModal');
            resetValidationState('newRequestModal');
            this.querySelector('form').reset();
        });
    }
    
    // Modal de festivos trabajados
    const holidayModal = document.getElementById('newHolidayModal');
    if (holidayModal) {
        // Manejar envío del formulario (descripción personalizada)
        const holidayForm = holidayModal.querySelector('form');
        if (holidayForm) {
            holidayForm.addEventListener('submit', function(e) {
                const select = this.querySelector('select[name="description"]');
                const customInput = this.querySelector('input[name="custom_description"]');
                
                if (select && customInput && select.value === 'custom' && customInput.value.trim()) {
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'description';
                    hiddenInput.value = customInput.value.trim();
                    this.appendChild(hiddenInput);
                    select.disabled = true;
                }
            });
        }
        
        holidayModal.addEventListener('hidden.bs.modal', function() {
            this.querySelector('form').reset();
            toggleCustomDescription(); // Reset custom description
        });
    }
    
    // Modal de recuperaciones
    const recoveryModal = document.getElementById('recoveryModal');
    if (recoveryModal) {
        recoveryModal.addEventListener('hidden.bs.modal', function() {
            clearDatePickers('recoveryModal');
            resetValidationState('recoveryModal');
            this.querySelector('form').reset();
        });
    }
    
    // Modal de dashboard (festivos)
    const dashboardModal = document.getElementById('dashboardHolidayModal');
    if (dashboardModal) {
        const form = dashboardModal.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                const select = this.querySelector('select[name="description"]');
                const customInput = this.querySelector('input[name="custom_description"]');
                
                if (select && customInput && select.value === 'custom' && customInput.value.trim()) {
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'description';
                    hiddenInput.value = customInput.value.trim();
                    this.appendChild(hiddenInput);
                    select.disabled = true;
                }
            });
        }
        
        dashboardModal.addEventListener('hidden.bs.modal', function() {
            this.querySelector('form').reset();
            toggleDashboardCustomDescription();
        });
    }
}

/**
 * Toggle descripción personalizada en festivos (modal principal)
 */
function toggleCustomDescription() {
    const select = document.querySelector('#newHolidayModal select[name="description"]');
    const customDiv = document.getElementById('customDescriptionDiv');
    
    if (!select || !customDiv) return;
    
    const customInput = customDiv.querySelector('input[name="custom_description"]');
    
    if (select.value === 'custom') {
        customDiv.classList.remove('d-none');
        if (customInput) customInput.required = true;
    } else {
        customDiv.classList.add('d-none');
        if (customInput) {
            customInput.required = false;
            customInput.value = '';
        }
    }
}

/**
 * Toggle descripción personalizada en dashboard
 */
function toggleDashboardCustomDescription() {
    const select = document.querySelector('#dashboardHolidayModal select[name="description"]');
    const customDiv = document.getElementById('dashboardCustomDescriptionDiv');
    
    if (!select || !customDiv) return;
    
    const customInput = customDiv.querySelector('input[name="custom_description"]');
    
    if (select.value === 'custom') {
        customDiv.classList.remove('d-none');
        if (customInput) customInput.required = true;
    } else {
        customDiv.classList.add('d-none');
        if (customInput) {
            customInput.required = false;
            customInput.value = '';
        }
    }
}

/**
 * Función para mostrar modal de festivos desde dashboard
 */
function showHolidayModal() {
    const modal = new bootstrap.Modal(document.getElementById('dashboardHolidayModal'));
    modal.show();
}

/**
 * Mostrar modal de recuperación
 */
function showRecoveryModal(holidayId, holidayDate, holidayDescription) {
    const modal = document.getElementById('recoveryModal');
    if (!modal) return;
    
    // Rellenar información del festivo
    const holidayInfo = document.getElementById('recoveryHolidayInfo');
    if (holidayInfo) {
        holidayInfo.textContent = `${holidayDate} - ${holidayDescription}`;
    }
    
    const form = document.getElementById('recoveryForm');
    if (form) {
        form.action = `/holidays/${holidayId}/create-recovery`;
    }
    
    // Limpiar formulario
    const recoveryPicker = modal.querySelector('.recovery-date-picker');
    const hiddenInput = modal.querySelector('input[name="recovery_date"]');
    const reasonTextarea = modal.querySelector('textarea[name="reason"]');
    
    if (recoveryPicker && recoveryPicker._flatpickr) {
        recoveryPicker._flatpickr.clear();
    }
    if (hiddenInput) hiddenInput.value = '';
    if (reasonTextarea) reasonTextarea.value = '';
    
    resetValidationState('recoveryModal');
    
    // Configurar date picker específicamente
    setTimeout(() => {
        if (recoveryPicker) {
            if (recoveryPicker._flatpickr) {
                recoveryPicker._flatpickr.destroy();
            }
            
            flatpickr(recoveryPicker, {
                ...singleConfig,
                onChange: function(selectedDates, dateStr, instance) {
                    if (selectedDates.length === 1) {
                        hiddenInput.value = formatDate(selectedDates[0]);
                        
                        // Mostrar fecha seleccionada de forma amigable
                        const dayStr = selectedDates[0].toLocaleDateString('es-ES');
                        instance.input.value = `${dayStr} (1 día de recuperación)`;
                        
                        // Validar fecha
                        validateRecoveryDate(holidayId);
                    }
                }
            });
        }
    }, 100);
    
    // Mostrar modal
    new bootstrap.Modal(modal).show();
}

/**
 * Cancelar solicitud de vacaciones
 */
function cancelRequest(requestId) {
    if (confirm('¿Cancelar esta solicitud de vacaciones?')) {
        fetch(`/requests/${requestId}/cancel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Error al cancelar la solicitud');
            }
        }).catch(error => {
            console.error('Error:', error);
            alert('Error de conexión al cancelar la solicitud');
        });
    }
}

// Exportar funciones globales necesarias
window.toggleCustomDescription = toggleCustomDescription;
window.toggleDashboardCustomDescription = toggleDashboardCustomDescription;
window.showHolidayModal = showHolidayModal;
window.showRecoveryModal = showRecoveryModal;
window.cancelRequest = cancelRequest;