frappe.views.calendar['Banquet'] = {
    field_map: {
        start: 'start_date',
        end: 'end_date',
        id: 'name',
        title: 'name',
        //description: 'customer_name',
        //status: 'status',
        //allDay: 'allDay',
        //color: '`tabBanquet Type`.color'
    },
    //gantt: false,
    filters: [
        {
            fieldtype: 'Data',
            fieldname: 'customer_name',
            label: __('Customer Name')
        }
    ],
    style_map: {
        '0': 'info',
        '1': 'standard',
        '2': 'danger'
    },
    options: {
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month'
        },
        editable: false,
        selectable: false,
    },
    //get_events_method: 'frappe.desk.calendar.get_events'
};
