// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Banquet', {
	// refresh: function(frm) {

	// },
	customer_contact: function (frm) {
		erpnext.utils.get_contact_display(frm, 'customer_contact', 'contact_display');
	},
	customer_address: function (frm) {
		erpnext.utils.get_address_display(frm, 'customer_address', 'address_display');
		//erpnext.utils.set_taxes_from_address(this.frm, "supplier_address", "supplier_address", "supplier_address");
	},
	/*start_date: function(frm) {
		if(frm.doc.start_date){
			erpnext.utils.copy_value_in_all_rows(frm.doc, frm.doc.doctype, frm.doc.name, "banquet_details", "start_time");
		}
	},
	end_date: function(frm) {
		if(frm.doc.end_date){
			erpnext.utils.copy_value_in_all_rows(frm.doc, frm.doc.doctype, frm.doc.name, "banquet_details", "end_time");
		}
	},*/


	import_from_template_button: function (frm) {
		new frappe.ui.form.MultiSelectDialog({
			doctype: "Banquet Template",
			target: frm,
			setters: {
				//company: frm.doc.company,
				banquet_type: frm.doc.banquet_type

			},
			//date_field: "transaction_date",
			/*get_query() {
				return {
					filters: { docstatus: ['!=', 2] }
				}
			},*/
			action(selections) {
				console.log(selections);
			}
		});
		//this.dialog.show();
	}

});

frappe.ui.form.on('Banquet Detail', {
	/*banquet_details_add(frm, cdt, cdn) {
		//let row = frappe.get_doc(cdt, cdn);
		let row = locals[cdt][cdn];
		if (row.type != 'Section Break' && frm.doc.start_date) {
			frappe.model.set_value(cdt, cdn, {
				start_time: frappe.datetime.get_datetime_as_string(frm.doc.start_date),
				end_time: frappe.datetime.get_datetime_as_string(frm.doc.start_date)
			});
		}
	},*/

	type: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, {
			linked_doc: null,
			//start_time: null,
			//end_time: null,
			uom: null
		});
	},
	linked_doc: function (frm, cdt, cdn) {
		//let row = locals[cdt][cdn];
		let row = frappe.get_doc(cdt, cdn);
		if (row.type == 'Item' && row.linked_doc) {
			frappe.db.get_value('Item', row.linked_doc, ['item_name', 'description', 'stock_uom'])
				.then(r => {
					//console.log(r.message.status) // Open
					frappe.model.set_value(cdt, cdn, {
						title: r.message.item_name,
						description: r.message.description,
						uom: r.message.stock_uom
					});
				})
		} else if (row.type == 'Restaurant Reservation' && row.linked_doc) {
			frappe.db.get_value('Restaurant Reservation', row.linked_doc, ['name', 'start_time', 'end_time', 'no_of_people'])
				.then(r => {
					//console.log(r.message.status) // Open
					frappe.model.set_value(cdt, cdn, {
						title: __('Restaurant Reservation'), //r.message.name,
						start_time: r.message.start_time,
						end_time: r.message.end_time,
						qty: r.message.no_of_people
					});
				})
		}
	}
});