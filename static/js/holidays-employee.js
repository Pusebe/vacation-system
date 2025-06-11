/**
 * JavaScript para empleados en la página de festivos
 */

function toggleCustomDescription() {
    const select = document.querySelector('select[name="description"]');
    const customDiv = document.getElementById('customDescriptionDiv');
    
    if (select.value === 'custom') {
        customDiv.classList.remove('d-none');
        customDiv.querySelector('input').required = true;
    } else {
        customDiv.classList.add('d-none');
        customDiv.querySelector('input').required = false;
    }
}

function showRecoveryModal(holidayId, holidayDate, holidayDescription) {
    document.getElementById('recoveryHolidayInfo').textContent = `${holidayDate} - ${holidayDescription}`;
    document.getElementById('recoveryForm').action = `/holidays/${holidayId}/create-recovery`;
    
    // Limpiar el formulario
    document.querySelector('input[name="recovery_date"]').value = '';
    document.querySelector('textarea[name="reason"]').value = '';
    
    // Establecer fecha mínima como mañana
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.querySelector('input[name="recovery_date"]').min = tomorrow.toISOString().split('T')[0];
    
    new bootstrap.Modal(document.getElementById('recoveryModal')).show();
}

// Inicialización cuando se carga el DOM
document.addEventListener('DOMContentLoaded', function() {
    // Ajustar la descripción al enviar el formulario
    const holidayForm = document.querySelector('#newHolidayModal form');
    if (holidayForm) {
        holidayForm.addEventListener('submit', function(e) {
            const select = document.querySelector('select[name="description"]');
            const customInput = document.querySelector('input[name="custom_description"]');
            
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

    // Validar fecha de recuperación
    const recoveryDateInput = document.querySelector('input[name="recovery_date"]');
    if (recoveryDateInput) {
        recoveryDateInput.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate <= today) {
                alert('La fecha de recuperación debe ser futura.');
                this.value = '';
                return;
            }
        });
    }
    
    // Agregar tooltips a los botones de recuperación
    const recoveryButtons = document.querySelectorAll('button[onclick*="showRecoveryModal"]');
    recoveryButtons.forEach(button => {
        button.title = 'Solicitar 1 día de recuperación por este festivo trabajado';
    });
    
    // Tooltips para botones deshabilitados
    const disabledButtons = document.querySelectorAll('button[disabled]');
    disabledButtons.forEach(button => {
        if (button.textContent.includes('Completada')) {
            button.title = 'Ya se completó la recuperación para este festivo';
        } else if (button.textContent.includes('En espera')) {
            button.title = 'Ya tienes una solicitud de recuperación pendiente para este festivo';
        }
    });
});