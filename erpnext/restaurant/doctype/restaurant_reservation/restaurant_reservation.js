// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Restaurant Reservation', {
	onload: function (frm) {
		frm.set_query('banquet', () => {
			return {
				filters: {
					start_date: ['<=', frm.doc.start_time],
					end_date: ['>=', frm.doc.end_time]
				}
			}
		});
		frm.set_query('assigned_tables', () => {
			return {
				//query: 'erpnext.restaurant.queries.free_tables_query',
				filters: {
					restaurant: frm.doc.restaurant,
					min_seating: ['<=', frm.doc.no_of_people],
					max_seating: ['>=', frm.doc.no_of_people]
				}
			}
		});
		frm.set_query('contact_person', () => {
			if (frm.doc.customer) {
				return {
					query: 'frappe.contacts.doctype.contact.contact.contact_query',
					filters: {
						link_doctype: 'Customer',
						link_name: frm.doc.customer
					}
				}
			}
		});
	},
	refresh: function (frm) {
		//if (frm.doc.status == 'Accepted' && frm.doc.assigned_tables.length == 0) {
		if (['Open', 'Accepted', 'Waitlisted'].includes(frm.doc.status) && frm.doc.assigned_tables.length == 0) {
			frm.add_custom_button(__('Auto-Assign Table'), () => {
				frm.call('assign_table', {
					save: true
				})
					.then(r => {
						if (r.message) {
							//let linked_doc = r.message;
							// do something with linked_doc
						}
						frm.reload_doc();
					});

			}, __("Restaurant Table"));

			frm.add_custom_button(__('Check Availability'), () => {
				frm.call('assign_table', {
					save: false
				})
					.then(r => {
						if (r.message) {
							//let linked_doc = r.message;
							// do something with linked_doc
						}
						//frm.reload_doc();
					});

			}, __("Restaurant Table"));
		}

		// New Status Buttons
		if (frm.doc.status == 'Open' || frm.doc.status == 'Waitlisted') {
			frm.add_custom_button(__('Accept'), () => {
				// Do something
				frm.set_value('status', 'Accepted').then(() => {
					frm.save('Update');
				});
			}, __('Status'));
		}
		if (frm.doc.status == 'Open') {
			frm.add_custom_button(__('Waitlist'), () => {
				// Do something
				frm.set_value('status', 'Waitlisted').then(() => {
					frm.save('Update');
				});
			}, __('Status'));
		}
		if (frm.doc.status == 'Open' || frm.doc.status == 'Waitlisted') {
			frm.add_custom_button(__('Reject'), () => {
				// Do something
				frm.set_value('status', 'Rejected').then(() => {
					frm.save('Update');
				});
			}, __('Status'));
		}
		// Next Document
		if (frm.doc.status == 'Accepted' /*|| frappe.datetime.get_diff(frappe.datetime.nowdate(), frm.doc.start_time) == 0*/) {
			frm.add_custom_button(__('Restaurant Stay'), () => {
				// Do something

			}, __('Create'));
		}

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
