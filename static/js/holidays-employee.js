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
    const recoveryInput = document.querySelector('#recoveryModal input[name="recovery_date"]');
    const reasonTextarea = document.querySelector('#recoveryModal textarea[name="reason"]');
    const resultDiv = document.getElementById('recovery-validation-result');
    const submitBtn = document.getElementById('submitRecoveryBtn');
    
    if (recoveryInput) recoveryInput.value = '';
    if (reasonTextarea) reasonTextarea.value = '';
    if (resultDiv) resultDiv.style.display = 'none';
    if (submitBtn) submitBtn.disabled = true;
    
    // Establecer fecha mínima como mañana
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (recoveryInput) {
        recoveryInput.min = tomorrow.toISOString().split('T')[0];
    }
    
    new bootstrap.Modal(document.getElementById('recoveryModal')).show();
}

function validateRecoveryDate(holidayId) {
    const recoveryInput = document.querySelector('#recoveryModal input[name="recovery_date"]');
    const resultDiv = document.getElementById('recovery-validation-result');
    const submitBtn = document.getElementById('submitRecoveryBtn');
    
    if (!recoveryInput || !resultDiv || !submitBtn) return;
    
    const recoveryDate = recoveryInput.value;
    
    if (!recoveryDate) {
        resultDiv.style.display = 'none';
        submitBtn.disabled = true;
        return;
    }
    
    // Mostrar loading
    resultDiv.style.display = 'block';
    resultDiv.className = 'alert alert-info';
    resultDiv.innerHTML = '<div class="d-flex align-items-center"><i class="ti ti-loader me-2"></i><div>Validando fecha...</div></div>';
    submitBtn.disabled = true;
    
    const url = holidayId ? 
        `/api/validate-recovery-date?recovery_date=${recoveryDate}&holiday_id=${holidayId}` :
        `/api/validate-dates?start_date=${recoveryDate}&end_date=${recoveryDate}&type=recovery`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            resultDiv.style.display = 'block';
            const isValid = data.valid !== undefined ? data.valid : data.available;
            
            if (isValid) {
                resultDiv.className = 'alert alert-success';
                resultDiv.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="ti ti-check me-2"></i>
                        <div>
                            <strong>Fecha válida</strong><br>
                            <small>${data.message}</small>
                        </div>
                    </div>
                `;
                submitBtn.disabled = false;
            } else {
                resultDiv.className = 'alert alert-danger';
                resultDiv.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="ti ti-x me-2"></i>
                        <div>
                            <strong>Fecha no válida</strong><br>
                            <small>${data.message}</small>
                        </div>
                    </div>
                `;
                submitBtn.disabled = true;
            }
        })
        .catch(error => {
            console.error('Error validando recuperación:', error);
            resultDiv.style.display = 'block';
            resultDiv.className = 'alert alert-warning';
            resultDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="ti ti-alert-triangle me-2"></i>
                    <div>
                        <strong>Error de conexión</strong><br>
                        <small>No se pudo validar la fecha. Inténtalo de nuevo.</small>
                    </div>
                </div>
            `;
            submitBtn.disabled = true;
        });
}

// Inicialización cuando se carga el DOM
document.addEventListener('DOMContentLoaded', function() {
    // Ajustar la descripción al enviar el formulario
    const holidayForm = document.querySelector('#newHolidayModal form');
    if (holidayForm) {
        holidayForm.addEventListener('submit', function(e) {
            const select = document.querySelector('select[name="description"]');
            const customInput = document.querySelector('input[name="custom_description"]');
            
            if (select && customInput && select.value === 'custom' && customInput.value.trim()) {
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
    const recoveryDateInput = document.querySelector('#recoveryModal input[name="recovery_date"]');
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
            
            // Obtener holiday ID del action del formulario
            const form = document.getElementById('recoveryForm');
            const action = form.action;
            const holidayId = action.match(/\/holidays\/(\d+)\//)?.[1];
            
            if (holidayId) {
                validateRecoveryDate(holidayId);
            }
        });
    }
    
    // Agregar tooltips a los botones de recuperación
    const recoveryButtons = document.querySelectorAll('button[onclick*="showRecoveryModal"]');
    recoveryButtons.forEach(button => {
        button.title = 'Solicitar 1 día de recuperación por este festivo trabajado';
    });
});