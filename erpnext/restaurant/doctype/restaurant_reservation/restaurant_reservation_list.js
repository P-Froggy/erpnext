frappe.listview_settings['Restaurant Reservation'] = {
    /*add_fields: [
        "sent_or_received", "recipients", "subject",
        "communication_medium", "communication_type",
        "sender", "seen", "reference_doctype", "reference_name",
        "has_attachment", "communication_date"
    ],*/

    filters: [
        ["start_time", ">=", frappe.datetime.nowdate()]
    ],

    get_indicator: function (doc) {
        if (doc.docstatus === 0) {
            return [__("Draft"), "red", "status,=,Draft"];
        } else if (doc.docstatus === 1) {
            if (doc.status === "Open") {
                return [__("Open"), "orange", "status,=,Open"];
            } else if (doc.status === 'Accepted') {
                return [__("Accepted"), "green", "status,=,Accepted"];
            } else if (doc.status === 'Waitlisted') {
                return [__("Waitlisted"), "orange", "status,=,Waitlisted"];
            } else if (doc.status === 'Rejected') {
                return [__("Rejected"), "red", "status,=,Rejected"];
            } else if (doc.status === 'No Show') {
                return [__("No Show"), "grey", "status,=,No Show"];
            }

        } else if (doc.docstatus === 2) {
            return [__("Cancelled"), "red", "status,=,Cancelled"];
        }
    },

    onload: function (listview) {

        // .add_menu_item
        listview.page.add_inner_button(__("Reservation Assistant"), () => {
            frappe.prompt([
                {
                    label: 'Restaurant',
                    fieldname: 'restaurant',
                    fieldtype: 'Link',
                    options: 'Restaurant',
                    reqd: 1,
                    default: listview.page.fields_dict.restaurant.value
                },
                {
                    label: 'No of people',
                    fieldname: 'no_of_people',
                    fieldtype: 'Int',
                    non_negative: 1,
                    reqd: 1,
                    default: 2
                },
                {
                    fieldtype: 'Column Break',
                },
                {
                    label: 'Start time',
                    fieldname: 'start_time',
                    fieldtype: 'Datetime',
                    reqd: 1,
                    default: frappe.datetime.add_days(frappe.datetime.nowdate(), 1) //listview.page.fields_dict.start_time.value
                },
                {
                    label: 'End time',
                    fieldname: 'end_time',
                    fieldtype: 'Datetime',
                    reqd: 0,
                    //default: frappe.datetime.add_days(frappe.datetime.nowdate(), 1) //listview.page.fields_dict.end_time
                }
            ], (values) => {
                frappe.call({
                    method: 'erpnext.restaurant.doctype.restaurant_reservation.restaurant_reservation.check_availability',
                    args: {
                        restaurant: values.restaurant,
                        no_of_people: values.no_of_people,
                        start_time: values.start_time,
                        end_time: values.end_time
                    },
                    // disable the button until the request is completed
                    btn: $('.primary-action'),
                    // freeze the screen until the request is completed
                    freeze: true,
                    callback: (r) => {
                        // on success
                        frappe.confirm((r.message == true ? __("A free table is available for the specified date. Do you want to make a reservation?") : __("There is no table available for the given data. Do you still want to make a reservation?")),
                            () => {
                                let reservation = frappe.model.get_new_doc("Restaurant Reservation");
                                reservation.restaurant = values.restaurant;
                                reservation.no_of_people = values.no_of_people;
                                reservation.start_time = values.start_time;
                                reservation.end_time = values.end_time;
                                frappe.set_route("Form", reservation.doctype, reservation.name);
                            })
                    },
                    error: (r) => {
                        // on error
                    }
                })

            })
        });


        // .add_menu_item
        listview.page.add_inner_button(__("Assign Tables"), () => {
            //var method = "erpnext.restaurant.doctype.restaurant_reservation.restaurant_reservation.assign_tables2";
            //listview.call_for_selected_items(method, { /*action: "Read"*/ });

            frappe.prompt([
                {
                    label: 'Restaurant',
                    fieldname: 'restaurant',
                    fieldtype: 'Link',
                    options: 'Restaurant',
                    reqd: 1,
                    default: listview.page.fields_dict.restaurant.value
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    label: 'Start time',
                    fieldname: 'start_time',
                    fieldtype: 'Datetime',
                    reqd: 1,
                    default: frappe.datetime.nowdate()
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    label: 'End time',
                    fieldname: 'end_time',
                    fieldtype: 'Datetime',
                    reqd: 1,
                    default: frappe.datetime.add_days(frappe.datetime.nowdate(), 1)
                },
                /*{
                    label: 'Assign reservations',
                    fieldname: 'save',
                    fieldtype: 'Check',
                    default: 0
                }*/
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
                    callback: (r) => {
                        // on success
                    },
                    error: (r) => {
                        // on error
                    }
                });

            })
        });

    },

    /*primary_action: function () {
        new frappe.views.CommunicationComposer({ doc: {} });
    }*/

};