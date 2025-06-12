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
        const editDepartmentForm = document.getElementById('editDepartmentForm');
        if (editDepartmentForm) {
            editDepartmentForm.action = `/admin/departments/${deptId}/edit`;
        }
        const editDeptName = document.getElementById('editDeptName');
        if (editDeptName) {
            editDeptName.value = deptName;
        }
        const editDeptMaxConcurrent = document.getElementById('editDeptMaxConcurrent');
        if (editDeptMaxConcurrent) {
            editDeptMaxConcurrent.value = maxConcurrent;
        }
        const editDeptVacationDays = document.getElementById('editDeptVacationDays');
        if (editDeptVacationDays) {
            editDeptVacationDays.value = vacationDays;
        }
    }

    /**
     * Poblar modal de editar empleado
     */
    populateEditEmployeeModal(empId, empName, empEmail, deptId, vacationDays, hireDate, isActive) {
        const editEmployeeForm = document.getElementById('editEmployeeForm');
        if (editEmployeeForm) {
            editEmployeeForm.action = `/admin/employees/${empId}/edit`;
        }
        const editEmpName = document.getElementById('editEmpName');
        if (editEmpName) {
            editEmpName.value = empName;
        }
        const editEmpEmail = document.getElementById('editEmpEmail');
        if (editEmpEmail) {
            editEmpEmail.value = empEmail;
        }
        const editEmpDepartment = document.getElementById('editEmpDepartment');
        if (editEmpDepartment) {
            editEmpDepartment.value = deptId;
        }
        const editEmpVacationDays = document.getElementById('editEmpVacationDays');
        if (editEmpVacationDays) {
            editEmpVacationDays.value = vacationDays === 'null' ? '' : vacationDays;
        }
        const editEmpHireDate = document.getElementById('editEmpHireDate');
        if (editEmpHireDate) {
            editEmpHireDate.value = hireDate;
        }
        const editEmpActive = document.getElementById('editEmpActive');
        if (editEmpActive) {
            editEmpActive.value = isActive ? '1' : '0';
        }
    }

    /**
     * Poblar modal de resetear contraseña
     */
    populateResetPasswordModal(empId, empName) {
        const resetPasswordUserName = document.getElementById('resetPasswordUserName');
        if (resetPasswordUserName) {
            resetPasswordUserName.textContent = empName;
        }
        const resetPasswordForm = document.getElementById('resetPasswordForm');
        if (resetPasswordForm) {
            resetPasswordForm.action = `/admin/employees/${empId}/reset-password`;
        }
    }

    /**
     * Configurar modal de solicitudes de admin
     */
    setupAdminRequestModal() {
        const employeeSelect = document.querySelector('#adminCreateRequestModal select[name="user_id"]');
        const typeSelect = document.querySelector('#adminCreateRequestModal select[name="type"]');
        
        if (employeeSelect) {
            this.loadEmployeesHolidaysData(employeeSelect);
            
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
        console.log(`🔍 Actualizando recovery option: ${availableHolidays} festivos disponibles`);
        
        const holidaySelector = document.getElementById('holidaySelector');
        
        if (availableHolidays > 0) {
            recoveryOption.disabled = false;
            recoveryOption.textContent = `Recuperación de festivo (${availableHolidays} disponibles)`;
            recoveryOption.style.color = '#2fb344'; // Verde
            console.log('✅ Recovery option habilitada');
        } else {
            recoveryOption.disabled = true;
            recoveryOption.textContent = customMessage || 'Recuperación de festivo (sin festivos disponibles)';
            recoveryOption.style.color = '#dc3545'; // Rojo
            console.log('❌ Recovery option deshabilitada - sin festivos');
            
            if (typeSelect.value === 'recovery') {
                console.log('🔄 Cambiando de recovery a vacation automáticamente');
                typeSelect.value = 'vacation';
                
                const tempAlert = document.createElement('div');
                tempAlert.className = 'alert alert-warning alert-dismissible mt-2';
                tempAlert.innerHTML = `
                    <i class="ti ti-alert-triangle me-2"></i>
                    <strong>Sin festivos:</strong> El empleado no tiene festivos disponibles para recuperación.
                    <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
                `;
                
                typeSelect.parentNode.appendChild(tempAlert);
                
                setTimeout(() => {
                    if (tempAlert.parentNode) {
                        tempAlert.remove();
                    }
                }, 8000);
            }
        }

        if (holidaySelector) {
            if (typeSelect.value === 'recovery' && availableHolidays > 0) {
                holidaySelector.classList.remove('d-none');
                this.loadEmployeeHolidays();
            } else {
                holidaySelector.classList.add('d-none');
            }
        }

        if (holidayWarning) {
            if (typeSelect.value === 'recovery' && availableHolidays > 0) {
                holidayWarning.style.display = 'block';
                const alertDiv = holidayWarning.querySelector('.alert');
                if (alertDiv) {
                    alertDiv.innerHTML = `
                        <i class="ti ti-alert-triangle me-2"></i>
                        <strong>Atención:</strong> Al aprobar esta recuperación se marcará el festivo seleccionado como usado.
                        <br><small class="text-muted">Festivos disponibles: ${availableHolidays}</smallbri>
                    `;
                }
                console.log('⚠️ Warning de uso de festivo mostrado');
            } else {
                holidayWarning.style.display = 'none';
                console.log('ℹ️ Warning ocultado');
            }
        }
    }

    /**
     * Cargar festivos disponibles del empleado seleccionado
     */
    loadEmployeeHolidays() {
        const employeeSelect = document.querySelector('#adminCreateRequestModal select[name="user_id"]');
        const holidaySelect = document.getElementById('holidaySelect');
        
        if (!employeeSelect || !employeeSelect.value || !holidaySelect) return;
        
        const userId = employeeSelect.value;
        
        holidaySelect.innerHTML = '<option value="">Cargando festivos...</option>';
        
        fetch(`/admin/api/employee/${userId}/available-holidays`)
            .then(response => response.json())
            .then(data => {
                holidaySelect.innerHTML = '<option value="">Seleccionar festivo...</option>';
                
                if (data.holidays && data.holidays.length > 0) {
                    data.holidays.forEach(holiday => {
                        const option = document.createElement('option');
                        option.value = holiday.id;
                        option.textContent = `${holiday.date} - ${holiday.description || 'Sin descripción'}`;
                        holidaySelect.appendChild(option);
                    });
                } else {
                    holidaySelect.innerHTML = '<option value="">No hay festivos disponibles</option>';
                }
            })
            .catch(error => {
                console.error('Error cargando festivos:', error);
                holidaySelect.innerHTML = '<option value="">Error cargando festivos</option>';
            });
    }

    /**
     * Manejar envío del formulario de festivos de admin
     */
    handleAdminHolidaySubmit(e) {
        const form = e.target;
        const select = form.querySelector('select[name="description"]');
        const customInput = form.querySelector('input[name="custom_description"]');
        
        if (select && customInput && select.value === 'custom' && customInput.value.trim()) {
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'description';
            hiddenInput.value = customInput.value.trim();
            form.appendChild(hiddenInput);
            
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
        const requestForm = document.querySelector('#adminCreateRequestModal form');
        if (requestForm) {
            requestForm.reset();
            const holidayWarning = document.querySelector('#adminCreateRequestModal #holidayWarning');
            if (holidayWarning) holidayWarning.style.display = 'none';
        }

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
    
    if (!modal || !content || !title) return;
    
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