/**
 * JavaScript para el calendario del dashboard
 * Maneja la inicialización y funcionalidades del calendario
 */

let dashboardCalendar;

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboardCalendar();
});

function initializeDashboardCalendar() {
    const calendarEl = document.getElementById('dashboard-calendar');
    if (!calendarEl) return;
    
    console.log('Inicializando calendario...');
    
    dashboardCalendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'es',
        height: 500,
        firstDay: 1, // Empezar el lunes
        headerToolbar: {
            left: 'prev,next',
            center: 'title',
            right: ''
        },
        dayMaxEvents: 2,
        moreLinkClick: 'popover',
        eventDisplay: 'block',
        events: {
            url: '/api/calendar-events',
            success: function(events) {
                console.log('Eventos cargados:', events);
                console.log('Número de eventos:', events.length);
            },
            failure: function(error) {
                console.error('Error al cargar los eventos del calendario:', error);
            }
        },
        eventDidMount: function(info) {
            console.log('Evento montado:', info.event.title, info.event.start);
            // Añadir tooltip
            info.el.title = `${info.event.title}\n${info.event.extendedProps.user || ''}\n${info.event.extendedProps.department || ''}`;
        },
        eventClick: function(info) {
            showQuickEventDetails(info.event);
        }
    });
    
    dashboardCalendar.render();
    console.log('Calendario renderizado');
}

function showQuickEventDetails(event) {
    const startDate = event.start.toLocaleDateString('es-ES');
    const endDate = event.end ? new Date(event.end.getTime() - 24*60*60*1000).toLocaleDateString('es-ES') : startDate;
    
    // Mostrar detalles en un tooltip o alert simple
    let details = `${event.title}\n`;
    details += `Fechas: ${startDate} - ${endDate}\n`;
    if (event.extendedProps.user) details += `Empleado: ${event.extendedProps.user}\n`;
    if (event.extendedProps.department) details += `Departamento: ${event.extendedProps.department}`;
    
    alert(details);
}