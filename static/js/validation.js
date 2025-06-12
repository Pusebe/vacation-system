// static/js/validation.js - Funciones de validación separadas y reutilizables

/**
 * Validación para vacaciones de empleados
 */
function validateVacationDates() {
    const startInput = document.querySelector('input[name="start_date"]');
    const endInput = document.querySelector('input[name="end_date"]');
    
    // Buscar el div de validación con diferentes IDs posibles
    let resultDiv = document.getElementById('validation-result') || 
                   document.getElementById('vacation-validation-result');
    
    // Buscar el botón de submit con diferentes IDs posibles  
    let submitBtn = document.getElementById('submitBtn') || 
                   document.getElementById('submitVacationBtn');
    
    // Verificar que existen los elementos
    if (!startInput || !endInput || !resultDiv || !submitBtn) {
        console.warn('Elementos de validación de vacaciones no encontrados');
        return;
    }
    
    const startDate = startInput.value;
    const endDate = endInput.value;
    
    if (!startDate || !endDate) {
        resultDiv.style.display = 'none';
        submitBtn.disabled = true;
        return;
    }
    
    // Mostrar loading
    resultDiv.style.display = 'block';
    resultDiv.className = 'alert alert-info';
    resultDiv.innerHTML = '<div class="d-flex align-items-center"><i class="ti ti-loader me-2"></i><div>Validando fechas...</div></div>';
    submitBtn.disabled = true;
    
    fetch(`/api/validate-dates?start_date=${startDate}&end_date=${endDate}&type=vacation`)
        .then(response => response.json())
        .then(data => {
            resultDiv.style.display = 'block';
            if (data.available) {
                resultDiv.className = 'alert alert-success';
                resultDiv.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="ti ti-check me-2"></i>
                        <div>
                            <strong>Fechas disponibles</strong><br>
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
                            <strong>Fechas no disponibles</strong><br>
                            <small>${data.message}</small>
                        </div>
                    </div>
                `;
                submitBtn.disabled = true;
            }
        })
        .catch(error => {
            console.error('Error validando fechas:', error);
            resultDiv.style.display = 'block';
            resultDiv.className = 'alert alert-warning';
            resultDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="ti ti-alert-triangle me-2"></i>
                    <div>
                        <strong>Error de conexión</strong><br>
                        <small>No se pudieron validar las fechas. Inténtalo de nuevo.</small>
                    </div>
                </div>
            `;
            submitBtn.disabled = true;
        });
}

/**
 * Validación para recuperaciones de festivos
 */
function validateRecoveryDate(holidayId) {
    const recoveryInput = document.querySelector('input[name="recovery_date"]');
    const resultDiv = document.getElementById('recovery-validation-result');
    const submitBtn = document.getElementById('submitRecoveryBtn');
    
    if (!recoveryInput || !resultDiv || !submitBtn) {
        console.warn('Elementos de validación de recuperación no encontrados');
        return;
    }
    
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

/**
 * Validación genérica para admins
 */
function validateDates() {
    console.warn('validateDates() genérica llamada - usar funciones específicas');
    // Fallback para compatibilidad
    if (typeof validateVacationDates === 'function') {
        validateVacationDates();
    }
}

/**
 * Funciones auxiliares para modales
 */
function resetValidationState(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Ocultar todos los divs de validación
    const validationDivs = modal.querySelectorAll('[id*="validation-result"]');
    validationDivs.forEach(div => div.style.display = 'none');
    
    // Deshabilitar botones de submit
    const submitBtns = modal.querySelectorAll('button[type="submit"]');
    submitBtns.forEach(btn => btn.disabled = true);
}

function enableSubmitButton(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    const submitBtn = modal.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = false;
}