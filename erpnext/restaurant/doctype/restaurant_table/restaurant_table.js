// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Restaurant Table', {
	onload: function(frm) {
		frm.set_query('table_combinations', () => {
			return {
				filters: {
					restaurant: frm.doc.restaurant,
					type: ['in', ['Standard', 'Reserve']]
				}
			}
		});
	},

	refresh: function (frm) {

		frm.add_custom_button(__('Change Restaurant / Table'), () => {
			frappe.prompt([
				{
					label: 'Restaurant',
					fieldname: 'restaurant',
					fieldtype: 'Link',
					options: 'Restaurant',
					reqd: 1
				},
				{
					label: 'Table Number',
					fieldname: 'table_no',
					fieldtype: 'Data',
					reqd: 1
				},
				{
					label: 'Merge with existing',
					fieldname: 'merge',
					fieldtype: 'Check'
				},
			], (values) => {
				console.log(values.restaurant, values.table_no);
				frm.call('rename_doc', { restaurant: values.restaurant, table_no: values.table_no, merge: values.merge })
					.then(r => {
						if (r.message) {
							frappe.set_route("Form", "Restaurant Table", r.message);
						}
					})

			})
		});

	}
});
