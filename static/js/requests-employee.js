/**
 * JavaScript para la página de solicitudes/vacaciones de empleados
 */

function toggleRequestType() {
    validateDates();
}

function validateDates() {
    const startDate = document.querySelector('input[name="start_date"]').value;
    const endDate = document.querySelector('input[name="end_date"]').value;
    const type = document.querySelector('select[name="type"]').value;
    const resultDiv = document.getElementById('validation-result');
    const submitBtn = document.getElementById('submitBtn');
    
    if (!startDate || !endDate || !type) {
        resultDiv.style.display = 'none';
        submitBtn.disabled = true;
        return;
    }
    
    fetch(`/api/validate-dates?start_date=${startDate}&end_date=${endDate}&type=${type}`)
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

function cancelRequest(requestId) {
    if (confirm('¿Cancelar esta solicitud?')) {
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
        });
    }
}