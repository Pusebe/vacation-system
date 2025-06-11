/**
 * JavaScript para la página de solicitudes de administradores
 */

function approveRequest(requestId) {
    if (confirm('¿Aprobar esta solicitud?')) {
        fetch(`/requests/${requestId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Error al aprobar la solicitud');
            }
        });
    }
}

function deleteRequest(requestId, userName) {
    if (confirm(`¿Eliminar la solicitud de ${userName}? Esta acción no se puede deshacer.`)) {
        fetch(`/requests/${requestId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Error al eliminar la solicitud');
            }
        });
    }
}

function showRejectModal(requestId, userName) {
    document.getElementById('rejectUserName').textContent = userName;
    document.getElementById('rejectForm').action = `/requests/${requestId}/reject`;
    new bootstrap.Modal(document.getElementById('rejectModal')).show();
}

function showEditModal(requestId, userName, type, status, startDate, endDate, reason) {
    document.getElementById('editRequestUser').textContent = userName;
    document.getElementById('editRequestForm').action = `/requests/${requestId}/edit`;
    document.getElementById('editRequestType').value = type;
    document.getElementById('editRequestStatus').value = status;
    document.getElementById('editRequestStartDate').value = startDate;
    document.getElementById('editRequestEndDate').value = endDate;
    document.getElementById('editRequestReason').value = reason;
    new bootstrap.Modal(document.getElementById('editRequestModal')).show();
}