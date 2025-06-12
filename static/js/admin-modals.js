/**
 * JavaScript para modales de administrador
 * Maneja validaciones y lógica específica de admin
 */

class AdminModalsManager {
    constructor() {
        this.employeeHolidaysData = new Map();
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupAdminRequestModal();
            this.setupAdminHolidayModal();
            this.setupDepartmentModals();
            this.setupEmployeeModals();
        });
    }

    /**
     * Configurar modales de departamentos
     */
    setupDepartmentModals() {
        // Modal de editar departamento
        const editDeptModal = document.getElementById('editDepartmentModal');
        if (editDeptModal) {
            editDeptModal.addEventListener('show.bs.modal', (event) => {
                const button = event.relatedTarget;
                const deptId = button.getAttribute('data-dept-id');
                const deptName = button.getAttribute('data-dept-name');
                const maxConcurrent = button.getAttribute('data-dept-max-concurrent');
                const vacationDays = button.getAttribute('data-dept-vacation-days');
                
                this.populateEditDepartmentModal(deptId, deptName, maxConcurrent, vacationDays);
            });
        }
    }

    /**
     * Configurar modales de empleados
     */
    setupEmployeeModals() {
        // Modal de editar empleado
        const editEmpModal = document.getElementById('editEmployeeModal');
        if (editEmpModal) {
            editEmpModal.addEventListener('show.bs.modal', (event) => {
                const button = event.relatedTarget;
                if (button && button.hasAttribute('data-emp-id')) {
                    const empId = button.getAttribute('data-emp-id');
                    const empName = button.getAttribute('data-emp-name');
                    const empEmail = button.getAttribute('data-emp-email');
                    const deptId = button.getAttribute('data-emp-dept-id');
                    const vacationDays = button.getAttribute('data-emp-vacation-days');
                    const hireDate = button.getAttribute('data-emp-hire-date');
                    const isActive = button.getAttribute('data-emp-active') === 'true';
                    
                    this.populateEditEmployeeModal(empId, empName, empEmail, deptId, vacationDays, hireDate, isActive);
                }
            });
        }

        // Modal de resetear contraseña
        const resetPasswordModal = document.getElementById('resetPasswordModal');
        if (resetPasswordModal) {
            resetPasswordModal.addEventListener('show.bs.modal', (event) => {
                const button = event.relatedTarget;
                if (button && button.hasAttribute('data-emp-id')) {
                    const empId = button.getAttribute('data-emp-id');
                    const empName = button.getAttribute('data-emp-name');
                    
                    this.populateResetPasswordModal(empId, empName);
                }
            });
        }
    }

    /**
     * Poblar modal de editar departamento
     */
    populateEditDepartmentModal(deptId, deptName, maxConcurrent, vacationDays) {
        document.getElementById('editDepartmentForm').action = `/admin/departments/${deptId}/edit`;
        document.getElementById('editDeptName').value = deptName;
        document.getElementById('editDeptMaxConcurrent').value = maxConcurrent;
        document.getElementById('editDeptVacationDays').value = vacationDays;
    }

    /**
     * Poblar modal de editar empleado
     */
    populateEditEmployeeModal(empId, empName, empEmail, deptId, vacationDays, hireDate, isActive) {
        document.getElementById('editEmployeeForm').action = `/admin/employees/${empId}/edit`;
        document.getElementById('editEmpName').value = empName;
        document.getElementById('editEmpEmail').value = empEmail;
        document.getElementById('editEmpDepartment').value = deptId;
        document.getElementById('editEmpVacationDays').value = vacationDays === 'null' ? '' : vacationDays;
        document.getElementById('editEmpHireDate').value = hireDate;
        document.getElementById('editEmpActive').value = isActive ? '1' : '0';
    }

    /**
     * Poblar modal de resetear contraseña
     */
    populateResetPasswordModal(empId, empName) {
        document.getElementById('resetPasswordUserName').textContent = empName;
        document.getElementById('resetPasswordForm').action = `/admin/employees/${empId}/reset-password`;
    }

    /**
     * Configurar modal de solicitudes de admin
     */
    setupAdminRequestModal() {
        const employeeSelect = document.querySelector('#adminCreateRequestModal select[name="user_id"]');
        const typeSelect = document.querySelector('#adminCreateRequestModal select[name="type"]');
        
        if (employeeSelect) {
            // Cargar datos de festivos disponibles
            this.loadEmployeesHolidaysData(employeeSelect);
            
            // Configurar eventos
            employeeSelect.addEventListener('change', () => {
                this.checkEmployeeHolidays();
            });

            if (typeSelect) {
                typeSelect.addEventListener('change', () => {
                    this.checkEmployeeHolidays();
                });
            }
        }
    }

    /**
     * Configurar modal de festivos de admin
     */
    setupAdminHolidayModal() {
        const adminHolidayForm = document.querySelector('#adminCreateHolidayModal form');
        if (adminHolidayForm) {
            adminHolidayForm.addEventListener('submit', (e) => {
                this.handleAdminHolidaySubmit(e);
            });
        }

        // Toggle para descripción personalizada
        const descSelect = document.querySelector('#adminCreateHolidayModal select[name="description"]');
        if (descSelect) {
            descSelect.addEventListener('change', () => {
                this.toggleAdminCustomDescription();
            });
        }
    }

    /**
     * Cargar datos de festivos disponibles para cada empleado
     */
    loadEmployeesHolidaysData(employeeSelect) {
        Array.from(employeeSelect.options).forEach(option => {
            if (option.value) {
                const userId = option.value;
                const availableHolidays = parseInt(option.getAttribute('data-available-holidays') || '0');
                this.employeeHolidaysData.set(userId, availableHolidays);
            }
        });
    }

    /**
     * Verificar festivos disponibles del empleado seleccionado
     */
    checkEmployeeHolidays() {
        const employeeSelect = document.querySelector('#adminCreateRequestModal select[name="user_id"]');
        const recoveryOption = document.querySelector('#adminCreateRequestModal #recoveryOption');
        const typeSelect = document.querySelector('#adminCreateRequestModal #adminRequestType');
        const holidayWarning = document.querySelector('#adminCreateRequestModal #holidayWarning');
        
        if (!employeeSelect || !recoveryOption || !typeSelect) return;

        if (!employeeSelect.value) {
            this.updateRecoveryOption(recoveryOption, typeSelect, holidayWarning, 0, 'Selecciona empleado');
            return;
        }

        const availableHolidays = this.employeeHolidaysData.get(employeeSelect.value) || 0;
        this.updateRecoveryOption(recoveryOption, typeSelect, holidayWarning, availableHolidays);
    }

    /**
     * Actualizar opción de recovery según festivos disponibles
     */
    updateRecoveryOption(recoveryOption, typeSelect, holidayWarning, availableHolidays, customMessage = null) {
        if (availableHolidays > 0) {
            recoveryOption.disabled = false;
            recoveryOption.textContent = `Recuperación de festivo (${availableHolidays} disponibles)`;
        } else {
            recoveryOption.disabled = true;
            recoveryOption.textContent = customMessage || 'Recuperación de festivo (sin festivos disponibles)';
            
            // Si tenía recovery seleccionado, cambiar a vacation
            if (typeSelect.value === 'recovery') {
                typeSelect.value = 'vacation';
            }
        }

        // Mostrar/ocultar warning
        if (holidayWarning) {
            if (typeSelect.value === 'recovery' && availableHolidays > 0) {
                holidayWarning.style.display = 'block';
            } else {
                holidayWarning.style.display = 'none';
            }
        }
    }

    /**
     * Manejar envío del formulario de festivos de admin
     */
    handleAdminHolidaySubmit(e) {
        const form = e.target;
        const select = form.querySelector('select[name="description"]');
        const customInput = form.querySelector('input[name="custom_description"]');
        
        if (select && customInput && select.value === 'custom' && customInput.value.trim()) {
            // Crear input hidden con la descripción personalizada
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'description';
            hiddenInput.value = customInput.value.trim();
            form.appendChild(hiddenInput);
            
            // Deshabilitar el select para que no envíe 'custom'
            select.disabled = true;
        }
    }

    /**
     * Toggle para descripción personalizada en modal de festivos
     */
    toggleAdminCustomDescription() {
        const select = document.querySelector('#adminCreateHolidayModal select[name="description"]');
        const customDiv = document.querySelector('#adminCreateHolidayModal #adminCustomDescriptionDiv');
        
        if (!select || !customDiv) return;
        
        if (select.value === 'custom') {
            customDiv.classList.remove('d-none');
            const input = customDiv.querySelector('input');
            if (input) input.required = true;
        } else {
            customDiv.classList.add('d-none');
            const input = customDiv.querySelector('input');
            if (input) input.required = false;
        }
    }

    /**
     * Limpiar formularios al cerrar modales
     */
    clearModalForms() {
        // Resetear formulario de solicitudes
        const requestForm = document.querySelector('#adminCreateRequestModal form');
        if (requestForm) {
            requestForm.reset();
            const holidayWarning = document.querySelector('#adminCreateRequestModal #holidayWarning');
            if (holidayWarning) holidayWarning.style.display = 'none';
        }

        // Resetear formulario de festivos
        const holidayForm = document.querySelector('#adminCreateHolidayModal form');
        if (holidayForm) {
            holidayForm.reset();
            this.toggleAdminCustomDescription();
        }
    }
}

// Instancia global
window.adminModalsManager = new AdminModalsManager();

// Funciones globales para compatibilidad con templates existentes
window.checkEmployeeHolidays = function() {
    window.adminModalsManager.checkEmployeeHolidays();
};

window.toggleAdminCustomDescription = function() {
    window.adminModalsManager.toggleAdminCustomDescription();
};

// Limpiar formularios al cerrar modales
document.addEventListener('hidden.bs.modal', function(event) {
    if (event.target.id === 'adminCreateRequestModal' || event.target.id === 'adminCreateHolidayModal') {
        window.adminModalsManager.clearModalForms();
    }
});

// ============================================================================
// FUNCIONES ESPECÍFICAS PARA EMPLEADOS
// ============================================================================

function showEditEmployeeModal(empId, name, email, deptId, vacationDays, hireDate, isActive) {
    if (window.adminModalsManager) {
        window.adminModalsManager.populateEditEmployeeModal(empId, name, email, deptId, vacationDays, hireDate, isActive);
    }
    new bootstrap.Modal(document.getElementById('editEmployeeModal')).show();
}

function showResetPasswordModal(empId, empName) {
    if (window.adminModalsManager) {
        window.adminModalsManager.populateResetPasswordModal(empId, empName);
    }
    new bootstrap.Modal(document.getElementById('resetPasswordModal')).show();
}

function deactivateEmployee(empId, empName) {
    if (confirm(`¿Desactivar a ${empName}? No podrá acceder al sistema.`)) {
        fetch(`/admin/employees/${empId}/deactivate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Error al desactivar el empleado');
            }
        });
    }
}

function reactivateEmployee(empId, empName) {
    if (confirm(`¿Reactivar a ${empName}? Podrá acceder nuevamente al sistema.`)) {
        fetch(`/admin/employees/${empId}/reactivate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Error al reactivar el empleado');
            }
        });
    }
}

async function showEmployeeBalance(empId, empName) {
    const modal = document.getElementById('employeeBalanceModal');
    const content = document.getElementById('employeeBalanceContent');
    const title = document.getElementById('employeeBalanceModalLabel');
    
    title.textContent = `Balance de Vacaciones - ${empName}`;
    content.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
    `;
    
    new bootstrap.Modal(modal).show();
    
    try {
        const response = await fetch(`/admin/api/employee/${empId}/vacation-balance`);
        const data = await response.json();
        
        if (data.success) {
            const balance = data.balance;
            content.innerHTML = `
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <div class="h2 text-primary">${balance.total_days}</div>
                                <div class="text-muted">Días totales</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <div class="h2 text-warning">${balance.used_days}</div>
                                <div class="text-muted">Días usados</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <div class="h2 ${balance.is_negative ? 'text-danger' : balance.available_days <= 5 ? 'text-warning' : 'text-success'}">${balance.available_days}</div>
                                <div class="text-muted">Días disponibles</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${balance.is_negative ? `
                    <div class="alert alert-danger mt-3">
                        <i class="ti ti-alert-triangle me-2"></i>
                        <strong>Balance negativo:</strong> Este empleado ha usado más días de los asignados para el año ${balance.year}.
                    </div>
                ` : ''}
                
                <div class="text-center mt-3 text-muted">
                    <small>Año ${balance.year}</small>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="alert alert-danger">
                    <i class="ti ti-alert-circle me-2"></i>
                    Error al cargar el balance: ${data.error || 'Error desconocido'}
                </div>
            `;
        }
    } catch (error) {
        content.innerHTML = `
            <div class="alert alert-danger">
                <i class="ti ti-wifi-off me-2"></i>
                Error de conexión. Inténtalo de nuevo.
            </div>
        `;
    }
}