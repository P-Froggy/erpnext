frappe.listview_settings['Restaurant Reservation'] = {
    /*add_fields: [
        "sent_or_received", "recipients", "subject",
        "communication_medium", "communication_type",
        "sender", "seen", "reference_doctype", "reference_name",
        "has_attachment", "communication_date"
    ],

    filters: [["status", "=", "Open"]],*/

    onload: function (listview) {
        listview.page.add_menu_item(__("Assign Tables"), () => {
            //var method = "erpnext.restaurant.doctype.restaurant_reservation.restaurant_reservation.assign_tables2";
            //listview.call_for_selected_items(method, { /*action: "Read"*/ });

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
                    callback: function (data) {
                        if (!data.exc) {
                            if (!data.message) {
                                frappe.msgprint(__('No Tables assigned'));
                            }
                            listview.refresh();
                        }
                    }
                });

            })
        });
    },

    /*primary_action: function () {
        new frappe.views.CommunicationComposer({ doc: {} });
    }*/

};