/**
 * Flatpickr simple para rangos de fechas
 * Implementación directa sin complicaciones
 */

class FlatpickrRanges {
    constructor() {
        this.instances = new Map();
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeAllRanges();
        });

        // Re-inicializar cuando se muestren modales
        document.addEventListener('shown.bs.modal', () => {
            setTimeout(() => this.initializeAllRanges(), 100);
        });

        // Limpiar al ocultar modales
        document.addEventListener('hidden.bs.modal', (event) => {
            this.clearModalInstances(event.target);
        });
    }

    initializeAllRanges() {
        // Buscar todos los inputs de rango de fechas
        const rangeInputs = document.querySelectorAll('.date-range-picker');
        
        rangeInputs.forEach(input => {
            if (!input._flatpickr && input.offsetParent !== null) { // Visible
                this.initRangePicker(input);
            }
        });

        // También buscar inputs individuales de recovery
        const recoveryInputs = document.querySelectorAll('.recovery-date-picker');
        
        recoveryInputs.forEach(input => {
            if (!input._flatpickr && input.offsetParent !== null) {
                this.initRecoveryPicker(input);
            }
        });
    }

    initRangePicker(input) {
        const modal = input.closest('.modal');
        const modalId = modal ? modal.id : 'unknown';
        
        // Buscar inputs ocultos para start_date y end_date
        const startHidden = modal.querySelector('input[name="start_date"]');
        const endHidden = modal.querySelector('input[name="end_date"]');
        
        if (!startHidden || !endHidden) {
            console.warn('No se encontraron inputs start_date/end_date en', modalId);
            return;
        }

        const config = {
            mode: 'range',
            locale: 'es',
            dateFormat: 'Y-m-d',
            minDate: 'today',
            showMonths: window.innerWidth > 768 ? 2 : 1,
            static: false,
            onChange: (selectedDates, dateStr, instance) => {
                this.handleRangeChange(selectedDates, input, startHidden, endHidden);
                this.validateDates(modal);
            },
            onReady: () => {
                // Cargar fechas existentes si las hay
                this.loadExistingDates(input, startHidden, endHidden);
            }
        };

        const fp = flatpickr(input, config);
        this.instances.set(input, fp);
        
        // 🎯 HACER CLICKEABLE EL ICONO TAMBIÉN
        this.makeIconClickable(input, fp);
        
        console.log(`✅ Range picker inicializado en ${modalId}`);
    }

    initRecoveryPicker(input) {
        const modal = input.closest('.modal');
        const modalId = modal ? modal.id : 'unknown';
        
        // Para recovery, buscar el input hidden recovery_date
        const recoveryHidden = modal.querySelector('input[name="recovery_date"]');
        
        if (!recoveryHidden) {
            console.warn('No se encontró input recovery_date en', modalId);
            return;
        }

        const config = {
            mode: 'single',
            locale: 'es',
            dateFormat: 'Y-m-d',
            minDate: 'today',
            static: false,
            onChange: (selectedDates, dateStr, instance) => {
                if (selectedDates.length === 1) {
                    const date = selectedDates[0];
                    const formatted = this.formatDate(date);
                    
                    recoveryHidden.value = formatted;
                    
                    // Mostrar fecha amigable
                    input.value = `${date.toLocaleDateString('es-ES')} (1 día de recuperación)`;
                    
                    this.validateRecovery(modal);
                }
            }
        };

        const fp = flatpickr(input, config);
        this.instances.set(input, fp);
        
        // 🎯 HACER CLICKEABLE EL ICONO TAMBIÉN
        this.makeIconClickable(input, fp);
        
        console.log(`✅ Recovery picker inicializado en ${modalId}`);
    }

    handleRangeChange(selectedDates, input, startHidden, endHidden) {
        if (selectedDates.length === 1) {
            // Solo inicio seleccionado
            const date = selectedDates[0];
            startHidden.value = this.formatDate(date);
            endHidden.value = '';
            
            input.value = `Desde ${date.toLocaleDateString('es-ES')} - Selecciona fecha fin`;
            
        } else if (selectedDates.length === 2) {
            // Rango completo
            const start = selectedDates[0];
            const end = selectedDates[1];
            
            startHidden.value = this.formatDate(start);
            endHidden.value = this.formatDate(end);
            
            const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
            input.value = `${start.toLocaleDateString('es-ES')} → ${end.toLocaleDateString('es-ES')} (${days} días)`;
        }
    }

    loadExistingDates(input, startHidden, endHidden) {
        const dates = [];
        
        if (startHidden.value) {
            dates.push(startHidden.value);
        }
        
        if (endHidden.value && endHidden.value !== startHidden.value) {
            dates.push(endHidden.value);
        }
        
        if (dates.length > 0) {
            const fp = this.instances.get(input);
            if (fp) {
                fp.setDate(dates, false);
                
                // Actualizar texto visual
                if (dates.length === 2) {
                    const start = new Date(dates[0]);
                    const end = new Date(dates[1]);
                    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
                    input.value = `${start.toLocaleDateString('es-ES')} → ${end.toLocaleDateString('es-ES')} (${days} días)`;
                } else {
                    const start = new Date(dates[0]);
                    input.value = `Desde ${start.toLocaleDateString('es-ES')} - Selecciona fecha fin`;
                }
            }
        }
    }

    validateDates(modal) {
        const startHidden = modal.querySelector('input[name="start_date"]');
        const endHidden = modal.querySelector('input[name="end_date"]');
        const validationDiv = modal.querySelector('#validation-result, #vacation-validation-result');
        const submitBtn = modal.querySelector('button[type="submit"]');
        
        if (!startHidden || !endHidden || !validationDiv || !submitBtn) return;
        
        const startDate = startHidden.value;
        const endDate = endHidden.value;
        
        if (!startDate || !endDate) {
            this.setValidationState(validationDiv, submitBtn, false, 'Selecciona ambas fechas');
            return;
        }
        
        // Validar con API
        const type = modal.querySelector('select[name="type"]')?.value || 'vacation';
        
        fetch(`/api/validate-dates?start_date=${startDate}&end_date=${endDate}&type=${type}`)
            .then(response => response.json())
            .then(data => {
                this.setValidationState(validationDiv, submitBtn, data.available, data.message);
            })
            .catch(error => {
                console.error('Error validando:', error);
                this.setValidationState(validationDiv, submitBtn, false, 'Error al validar fechas');
            });
    }

    validateRecovery(modal) {
        const recoveryHidden = modal.querySelector('input[name="recovery_date"]');
        const validationDiv = modal.querySelector('#recovery-validation-result, #validation-result');
        const submitBtn = modal.querySelector('button[type="submit"]');
        
        if (!recoveryHidden || !validationDiv || !submitBtn) return;
        
        const recoveryDate = recoveryHidden.value;
        
        if (!recoveryDate) {
            this.setValidationState(validationDiv, submitBtn, false, 'Selecciona la fecha de recuperación');
            return;
        }
        
        // Validar con API específica de recovery
        const url = `/api/validate-recovery-date?recovery_date=${recoveryDate}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.setValidationState(validationDiv, submitBtn, data.valid, data.message);
            })
            .catch(error => {
                console.error('Error validando recovery:', error);
                this.setValidationState(validationDiv, submitBtn, false, 'Error al validar fecha');
            });
    }

    setValidationState(validationDiv, submitBtn, isValid, message) {
        validationDiv.style.display = 'block';
        validationDiv.className = `alert alert-${isValid ? 'success' : 'danger'}`;
        validationDiv.innerHTML = `<i class="ti ti-${isValid ? 'check' : 'x'} me-2"></i>${message}`;
        
        if (submitBtn) {
            submitBtn.disabled = !isValid;
        }
    }

    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    makeIconClickable(input, flatpickrInstance) {
        // Buscar el icono en el input-group
        const inputGroup = input.closest('.input-group');
        if (!inputGroup) return;
        
        const icon = inputGroup.querySelector('.input-group-text');
        if (!icon) return;
        
        // Hacer clickeable el icono
        icon.style.cursor = 'pointer';
        icon.addEventListener('click', () => {
            flatpickrInstance.open();
        });
        
        console.log('🎯 Icono clickeable configurado');
    }

    clearModalInstances(modal) {
        const inputs = modal.querySelectorAll('.date-range-picker, .recovery-date-picker');
        inputs.forEach(input => {
            const fp = this.instances.get(input);
            if (fp) {
                fp.destroy();
                this.instances.delete(input);
            }
        });
    }

    destroy() {
        this.instances.forEach(fp => fp.destroy());
        this.instances.clear();
    }
}

// Instancia global
window.flatpickrRanges = new FlatpickrRanges();

// Funciones de compatibilidad para código existente
window.validateDates = function() {
    const activeModal = document.querySelector('.modal.show');
    if (activeModal) {
        window.flatpickrRanges.validateDates(activeModal);
    }
};

window.validateVacationDates = function() {
    window.validateDates();
};

window.validateRecoveryDate = function() {
    const activeModal = document.querySelector('.modal.show');
    if (activeModal) {
        window.flatpickrRanges.validateRecovery(activeModal);
    }
};

window.toggleRequestType = function() {
    // El tipo cambió, re-validar
    setTimeout(() => window.validateDates(), 100);
};