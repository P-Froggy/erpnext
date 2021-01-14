// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Restaurant Reservation', {
	onload: function (frm) {
		frm.set_query('assigned_tables', () => {
			return {
				query: 'erpnext.restaurant.doctype.restaurant_reservation.restaurant_reservation.free_tables_query',
				filters: {
					restaurant: frm.doc.restaurant
				}
			}
		});
	},
	refresh: function (frm) {
		frm.add_custom_button(__('Auto-Assign Tables'), () => {
			frappe.prompt([
				{
					label: 'Restaurant',
					fieldname: 'restaurant',
					fieldtype: 'Link',
					options: 'Restaurant',
					reqd: 1
				},
				{
					label: 'Start time',
					fieldname: 'start_time',
					fieldtype: 'Datetime',
					reqd: 1
				},
				{
					label: 'End time',
					fieldname: 'end_time',
					fieldtype: 'Datetime',
					reqd: 1
				},
				{
					label: 'Assign reservations',
					fieldname: 'save',
					fieldtype: 'Check',
					default: 0
				}
			], (values) => {
				frappe.call({
					method: "erpnext.restaurant.doctype.restaurant_reservation.restaurant_reservation.assign_tables",
					args: {
						restaurant: values.restaurant,
						start_time: values.start_time,
						end_time: values.end_time,
						save: values.save
					},
					freeze: true,
					callback: function (r) {
						if (r.message) {
							frappe.msgprint({
								title: __('Notification'),
								indicator: 'green',
								message: __(r.message)
							});
						}
						frm.reload_doc();
					}
				});

			})
		});

	},
	/*setup_queries: function(doc, cdt, cdn) {
		this.frm.set_query("restaurant_table", "assigned_tables", function() {
			return{
				query: "erpnext.restaurant.restaurant_reservation.restaurant_reservation.free_tables_query",
				//filters:{ 'is_sub_contracted_item': 1 }
			}		

		});

	}*/
});
