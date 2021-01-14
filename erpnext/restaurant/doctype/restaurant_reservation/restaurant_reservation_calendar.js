frappe.views.calendar["Restaurant Reservation"] = {
	field_map: {
		"start": "start_time",
		"end": "end_time",
		"id": "name",
		"title": "customer_name",
		"description": "assigned_tables",
		//"allDay": "allDay",
	},
	gantt: true,
	filters: [
		{
			"fieldtype": "Data",
			"fieldname": "customer_name",
			"label": __("Customer Name")
		}
	],
	get_events_method: "frappe.desk.calendar.get_events"
};
