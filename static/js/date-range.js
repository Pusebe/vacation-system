/**
 * Componente híbrido de rangos de fechas
 * Mantiene inputs nativos type="date" + overlay visual para selección de rango
 */

class DateRangeManager {
    constructor() {
        this.instances = new Map();
        this.validators = new Map();
        this.overlayPicker = null;
    }

    /**
     * Inicializar rango híbrido: inputs nativos + overlay de rango SOLO SI NO ES ADMIN
     */
    initRange(config) {
        const {
            startInput,
            endInput,
            validationDiv,
            submitBtn,
            type = 'vacation',
            onValidate,
            flatpickrOptions = {}
        } = config;

        const startEl = document.querySelector(startInput);
        const endEl = document.querySelector(endInput);
        
        if (!startEl || !endEl) {
            console.warn('DateRange: No se encontraron los inputs especificados');
            return null;
        }

        // VERIFICAR SI ES MODAL DE ADMIN - NO aplicar overlay complicado
        const isAdminModal = startEl.closest('#adminCreateRequestModal') !== null;
        
        if (isAdminModal) {
            console.log('Modal de admin detectado - usando inputs nativos simples');
            // Para admin: solo configurar validación, sin overlay
            this._setupNativeValidation(startEl, endEl, config);
            return {
                validate: () => this._validateRange(config),
                destroy: () => this.destroyRange(`${startInput}-${endInput}`)
            };
        }

        // Para empleados: sistema completo con overlay
        const rangeId = `${startInput}-${endInput}`;
        
        // Configurar eventos para abrir overlay
        this._setupOverlayTriggers(startEl, endEl, config);

        // Configurar validación en inputs nativos
        this._setupNativeValidation(startEl, endEl, config);

        // Guardar instancia
        this.instances.set(rangeId, {
            startEl,
            endEl,
            config,
            type
        });

        // Configurar validador
        if (validationDiv || onValidate) {
            this.validators.set(rangeId, {
                validationDiv: validationDiv ? document.querySelector(validationDiv) : null,
                submitBtn: submitBtn ? document.querySelector(submitBtn) : null,
                onValidate,
                type
            });
        }

        return {
            validate: () => this._validateRange(config),
            destroy: () => this.destroyRange(rangeId)
        };
    }

    /**
     * Configurar triggers para abrir overlay de rango
     */
    _setupOverlayTriggers(startEl, endEl, config) {
        // DETECTAR SI ES MÓVIL - en móvil usar inputs nativos
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
                         window.innerWidth <= 768;
        
        if (isMobile) {
            console.log('Dispositivo móvil detectado - usando inputs nativos');
            // En móvil: permitir que funcionen los inputs nativos normalmente
            return;
        }
        
        // Solo en desktop: interceptar y mostrar overlay
        const self = this;
        [startEl, endEl].forEach(input => {
            input.addEventListener('focus', (e) => {
                e.preventDefault();
                input.blur();
                setTimeout(() => {
                    self._showRangeOverlay(startEl, endEl, config);
                }, 50);
            });
            
            input.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                input.blur();
                setTimeout(() => {
                    self._showRangeOverlay(startEl, endEl, config);
                }, 50);
            });

            input.addEventListener('mousedown', (e) => {
                e.preventDefault();
            });
        });
    }

    /**
     * Configurar validación en inputs nativos
     */
    _setupNativeValidation(startEl, endEl, config) {
        // Validar cuando cambian los inputs nativos
        [startEl, endEl].forEach(input => {
            input.addEventListener('change', () => {
                this._validateRange(config);
            });
        });
    }

    /**
     * Mostrar overlay de selección de rango
     */
    _showRangeOverlay(startEl, endEl, config) {
        // Destruir overlay anterior si existe
        if (this.overlayPicker) {
            this.overlayPicker.destroy();
        }

        // Crear elemento temporal invisible para el overlay
        const tempInput = document.createElement('input');
        tempInput.type = 'text';
        tempInput.style.position = 'absolute';
        tempInput.style.opacity = '0';
        tempInput.style.pointerEvents = 'none';
        tempInput.style.top = '-9999px';
        document.body.appendChild(tempInput);

        // Configurar Flatpickr en modo range sobre el elemento temporal
        const flatpickrConfig = {
            mode: config.type === 'recovery' ? 'single' : 'range',
            locale: 'es',
            dateFormat: 'Y-m-d',
            inline: false,
            minDate: 'today',
            defaultDate: this._getDefaultDates(startEl, endEl, config.type),
            onChange: (selectedDates, dateStr, instance) => {
                this._handleOverlaySelection(selectedDates, startEl, endEl, config);
            },
            onClose: () => {
                setTimeout(() => {
                    if (this.overlayPicker) {
                        this.overlayPicker.destroy();
                        this.overlayPicker = null;
                        if (tempInput.parentNode) {
                            tempInput.parentNode.removeChild(tempInput);
                        }
                    }
                }, 100);
            }
        };

        // Crear y abrir overlay
        this.overlayPicker = flatpickr(tempInput, flatpickrConfig);
        this.overlayPicker.open();

        // Posicionar el calendario cerca del input clickeado
        setTimeout(() => {
            this._positionOverlay(startEl);
        }, 50);
    }

    /**
     * Obtener fechas por defecto para el overlay
     */
    _getDefaultDates(startEl, endEl, type) {
        const dates = [];
        
        if (startEl.value) {
            dates.push(startEl.value);
        }
        
        if (type !== 'recovery' && endEl.value && endEl.value !== startEl.value) {
            dates.push(endEl.value);
        }
        
        return dates.length > 0 ? dates : null;
    }

    /**
     * Posicionar overlay cerca del input
     */
    _positionOverlay(inputEl) {
        if (!this.overlayPicker || !this.overlayPicker.calendarContainer) return;

        const calendar = this.overlayPicker.calendarContainer;
        const inputRect = inputEl.getBoundingClientRect();
        
        calendar.style.position = 'fixed';
        calendar.style.top = (inputRect.bottom + 5) + 'px';
        calendar.style.left = inputRect.left + 'px';
        calendar.style.zIndex = '9999';
    }

    /**
     * Manejar selección en overlay y poblar inputs nativos
     */
    _handleOverlaySelection(selectedDates, startEl, endEl, config) {
        if (config.type === 'recovery') {
            // Recuperación: una fecha en ambos inputs
            if (selectedDates.length === 1) {
                const date = this._formatDate(selectedDates[0]);
                startEl.value = date;
                endEl.value = date;
                
                // Disparar eventos de cambio en inputs nativos
                startEl.dispatchEvent(new Event('change', { bubbles: true }));
                endEl.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Cerrar overlay
                if (this.overlayPicker) {
                    this.overlayPicker.close();
                }
            }
        } else {
            // Vacaciones: rango de fechas
            if (selectedDates.length === 1) {
                // Solo inicio seleccionado
                startEl.value = this._formatDate(selectedDates[0]);
                startEl.dispatchEvent(new Event('change', { bubbles: true }));
            } else if (selectedDates.length === 2) {
                // Rango completo
                startEl.value = this._formatDate(selectedDates[0]);
                endEl.value = this._formatDate(selectedDates[1]);
                
                // Disparar eventos de cambio
                startEl.dispatchEvent(new Event('change', { bubbles: true }));
                endEl.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Cerrar overlay
                if (this.overlayPicker) {
                    this.overlayPicker.close();
                }
            }
        }
    }

    /**
     * Formatear fecha para input type="date"
     */
    _formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * Validar rango usando los valores de inputs nativos
     */
    async _validateRange(config) {
        const { startInput, endInput, type } = config;
        const rangeId = `${startInput}-${endInput}`;
        const validator = this.validators.get(rangeId);
        
        if (!validator) return;

        const startEl = document.querySelector(startInput);
        const endEl = document.querySelector(endInput);
        const { validationDiv, submitBtn, onValidate } = validator;

        const startDate = startEl.value;
        const endDate = endEl.value;

        // Limpiar estados anteriores
        this._clearValidationState(startEl, endEl, validationDiv, submitBtn);

        if (!startDate || !endDate) {
            this._setValidationState(false, 'Selecciona ambas fechas', startEl, endEl, validationDiv, submitBtn);
            return;
        }

        // Validación básica de rango
        if (new Date(startDate) > new Date(endDate)) {
            this._setValidationState(false, 'La fecha de inicio no puede ser posterior a la de fin', startEl, endEl, validationDiv, submitBtn);
            return;
        }

        // Para recuperaciones, validar que sea solo 1 día
        if (type === 'recovery' && startDate !== endDate) {
            this._setValidationState(false, 'Las recuperaciones solo pueden ser de 1 día', startEl, endEl, validationDiv, submitBtn);
            return;
        }

        // Validación personalizada o con API
        if (onValidate) {
            try {
                const result = await onValidate(startDate, endDate, type);
                this._setValidationState(result.valid, result.message, startEl, endEl, validationDiv, submitBtn);
            } catch (error) {
                this._setValidationState(false, 'Error al validar fechas', startEl, endEl, validationDiv, submitBtn);
            }
        } else {
            this._validateWithAPI(startDate, endDate, type, startEl, endEl, validationDiv, submitBtn);
        }
    }

    /**
     * Validar con API del backend
     */
    async _validateWithAPI(startDate, endDate, type, startEl, endEl, validationDiv, submitBtn) {
        try {
            const response = await fetch(`/api/validate-dates?start_date=${startDate}&end_date=${endDate}&type=${type}`);
            const data = await response.json();
            
            this._setValidationState(data.available, data.message, startEl, endEl, validationDiv, submitBtn);
        } catch (error) {
            console.error('Error validating dates:', error);
            this._setValidationState(false, 'Error al validar fechas', startEl, endEl, validationDiv, submitBtn);
        }
    }

    /**
     * Establecer estado de validación
     */
    _setValidationState(isValid, message, startEl, endEl, validationDiv, submitBtn) {
        // Actualizar div de validación
        if (validationDiv) {
            validationDiv.style.display = 'block';
            validationDiv.className = `alert alert-${isValid ? 'success' : 'danger'}`;
            validationDiv.innerHTML = `<i class="ti ti-${isValid ? 'check' : 'x'} me-2"></i>${message}`;
        }

        // Actualizar botón
        if (submitBtn) {
            submitBtn.disabled = !isValid;
        }
    }

    /**
     * Limpiar estado de validación
     */
    _clearValidationState(startEl, endEl, validationDiv, submitBtn) {
        if (validationDiv) {
            validationDiv.style.display = 'none';
        }

        if (submitBtn) {
            submitBtn.disabled = true;
        }
    }

    /**
     * Destruir rango
     */
    destroyRange(rangeId) {
        const instance = this.instances.get(rangeId);
        if (instance) {
            this.instances.delete(rangeId);
            this.validators.delete(rangeId);
        }
        
        if (this.overlayPicker) {
            this.overlayPicker.destroy();
            this.overlayPicker = null;
        }
    }

    /**
     * Destruir todas las instancias
     */
    destroyAll() {
        this.instances.forEach((instance, rangeId) => {
            this.destroyRange(rangeId);
        });
    }

    /**
     * Métodos de conveniencia
     */
    initVacationRange(modalId, options = {}) {
        return this.initRange({
            startInput: `${modalId} input[name="start_date"]`,
            endInput: `${modalId} input[name="end_date"]`,
            validationDiv: `${modalId} #validation-result, ${modalId} #vacation-validation-result`,
            submitBtn: `${modalId} button[type="submit"]`,
            type: 'vacation',
            ...options
        });
    }

    initRecoveryRange(modalId, options = {}) {
        // Para recuperaciones, buscar el input correcto
        const modal = document.querySelector(modalId);
        if (!modal) return null;
        
        const recoveryInput = modal.querySelector('input[name="recovery_date"]');
        if (recoveryInput) {
            // Si hay input de recovery_date, usar ese
            return this.initRange({
                startInput: `${modalId} input[name="recovery_date"]`,
                endInput: `${modalId} input[name="recovery_date"]`,
                validationDiv: `${modalId} #validation-result`,
                submitBtn: `${modalId} button[type="submit"]`,
                type: 'recovery',
                ...options
            });
        } else {
            // Si no, usar start_date y end_date en modo recovery
            return this.initRange({
                startInput: `${modalId} input[name="start_date"]`,
                endInput: `${modalId} input[name="end_date"]`,
                validationDiv: `${modalId} #validation-result`,
                submitBtn: `${modalId} button[type="submit"]`,
                type: 'recovery',
                ...options
            });
        }
    }
}

// Instancia global
window.dateRangeManager = new DateRangeManager();

// Funciones de conveniencia globales
window.initDateRange = (config) => window.dateRangeManager.initRange(config);
window.initVacationRange = (modalId, options) => window.dateRangeManager.initVacationRange(modalId, options);
window.initRecoveryRange = (modalId, options) => window.dateRangeManager.initRecoveryRange(modalId, options);

// Auto-inicialización
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        initializeDateRanges();
    }, 100);
});

function initializeDateRanges() {
    // Buscar modales con inputs de fecha
    const dateInputPairs = document.querySelectorAll('input[name="start_date"]');
    
    dateInputPairs.forEach(startInput => {
        const modal = startInput.closest('.modal');
        if (!modal) return;
        
        // SALTARSE MODALES DE ADMIN
        if (modal.id === 'adminCreateRequestModal') {
            console.log('Saltando modal de admin para date-range');
            return;
        }
        
        const endInput = modal.querySelector('input[name="end_date"]');
        const typeSelect = modal.querySelector('select[name="type"]');
        const validationDiv = modal.querySelector('#validation-result, #vacation-validation-result');
        const submitBtn = modal.querySelector('button[type="submit"]');
        
        if (endInput) {
            const modalId = `#${modal.id}`;
            
            if (typeSelect) {
                // Modal con selector de tipo
                typeSelect.addEventListener('change', function() {
                    const currentType = this.value;
                    if (currentType) {
                        const rangeId = `${modalId} input[name="start_date"]-${modalId} input[name="end_date"]`;
                        window.dateRangeManager.destroyRange(rangeId);
                        
                        window.dateRangeManager.initRange({
                            startInput: `${modalId} input[name="start_date"]`,
                            endInput: `${modalId} input[name="end_date"]`,
                            validationDiv: validationDiv ? `#${validationDiv.id}` : null,
                            submitBtn: submitBtn ? `${modalId} button[type="submit"]` : null,
                            type: currentType
                        });
                    }
                });
            } else {
                // Modal solo de vacaciones
                window.dateRangeManager.initRange({
                    startInput: `${modalId} input[name="start_date"]`,
                    endInput: `${modalId} input[name="end_date"]`,
                    validationDiv: validationDiv ? `#${validationDiv.id}` : null,
                    submitBtn: submitBtn ? `${modalId} button[type="submit"]` : null,
                    type: 'vacation'
                });
            }
        }
    });
    
    // Buscar inputs de recovery_date
    const recoveryInputs = document.querySelectorAll('input[name="recovery_date"]');
    recoveryInputs.forEach(input => {
        const modal = input.closest('.modal');
        if (!modal) return;
        
        const modalId = `#${modal.id}`;
        
        window.dateRangeManager.initRange({
            startInput: `${modalId} input[name="recovery_date"]`,
            endInput: `${modalId} input[name="recovery_date"]`,
            type: 'recovery'
        });
    });
}

// Limpiar al cerrar modales
document.addEventListener('hidden.bs.modal', function(event) {
    const modal = event.target;
    const modalId = `#${modal.id}`;
    
    window.dateRangeManager.instances.forEach((instance, rangeId) => {
        if (rangeId.includes(modalId)) {
            window.dateRangeManager.destroyRange(rangeId);
        }
    });
});

// Re-inicializar al mostrar modales
document.addEventListener('shown.bs.modal', function(event) {
    setTimeout(() => {
        initializeDateRanges();
    }, 100);
});

// Funciones de compatibilidad para código existente
window.validateDates = function() {
    const activeModal = document.querySelector('.modal.show');
    if (!activeModal) return;
    
    const modalId = `#${activeModal.id}`;
    const rangeId = `${modalId} input[name="start_date"]-${modalId} input[name="end_date"]`;
    const instance = window.dateRangeManager.instances.get(rangeId);
    
    if (instance) {
        window.dateRangeManager._validateRange(instance.config);
    }
};

window.validateVacationDates = function() {
    const activeModal = document.querySelector('.modal.show');
    if (!activeModal) return;
    
    const startInput = activeModal.querySelector('input[name="start_date"]');
    const endInput = activeModal.querySelector('input[name="end_date"]');
    
    if (startInput && endInput) {
        const modalId = `#${activeModal.id}`;
        window.dateRangeManager._validateRange({
            startInput: `${modalId} input[name="start_date"]`,
            endInput: `${modalId} input[name="end_date"]`,
            type: 'vacation'
        });
    }
};

window.toggleRequestType = function() {
    window.validateDates();
};