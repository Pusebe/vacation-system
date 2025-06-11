/**
 * JavaScript específico para Dashboard de Empleados
 * Maneja validaciones y funcionalidades de modales
 */

// Validación para vacaciones
function validateVacationDates() {
    const startDate = document.querySelector('#newVacationModal input[name="start_date"]').value;
    const endDate = document.querySelector('#newVacationModal input[name="end_date"]').value;
    const resultDiv = document.getElementById('vacation-validation-result');
    const submitBtn = document.getElementById('submitVacationBtn');
    
    if (!startDate || !endDate) {
        resultDiv.style.display = 'none';
        submitBtn.disabled = true;
        return;
    }
    
    fetch(`/api/validate-dates?start_date=${startDate}&end_date=${endDate}&type=vacation`)
        .then(response => response.json())
        .then(data => {
            resultDiv.style.display = 'block';
            if (data.available) {
                resultDiv.className = 'alert alert-success';
                resultDiv.innerHTML = `<i class="ti ti-check me-2"></i>${data.message}`;
                submitBtn.disabled = false;
            } else {
                resultDiv.className = 'alert alert-danger';
                resultDiv.innerHTML = `<i class="ti ti-x me-2"></i>${data.message}`;
                submitBtn.disabled = true;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultDiv.style.display = 'block';
            resultDiv.className = 'alert alert-warning';
            resultDiv.innerHTML = '<i class="ti ti-alert-triangle me-2"></i>Error al validar fechas';
            submitBtn.disabled = true;
        });
}

// Validación para festivos
function toggleHolidayCustomDescription() {
    const select = document.querySelector('#newHolidayModal select[name="description"]');
    const customDiv = document.getElementById('holidayCustomDescriptionDiv');
    
    if (!select || !customDiv) return;
    
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
    // Ajustar descripción al enviar formulario de festivos
    const holidayForm = document.querySelector('#newHolidayModal form');
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
    
    // Limpiar modales al cerrarlos
    const vacationModal = document.getElementById('newVacationModal');
    const holidayModal = document.getElementById('newHolidayModal');
    
    if (vacationModal) {
        vacationModal.addEventListener('hidden.bs.modal', function() {
            // Limpiar formulario de vacaciones
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                document.getElementById('vacation-validation-result').style.display = 'none';
                document.getElementById('submitVacationBtn').disabled = true;
            }
        });
    }
    
    if (holidayModal) {
        holidayModal.addEventListener('hidden.bs.modal', function() {
            // Limpiar formulario de festivos
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                const customDiv = document.getElementById('holidayCustomDescriptionDiv');
                if (customDiv) {
                    customDiv.classList.add('d-none');
                    customDiv.querySelector('input').required = false;
                }
            }
        });
    }
    
    console.log('Dashboard empleado inicializado correctamente');
});