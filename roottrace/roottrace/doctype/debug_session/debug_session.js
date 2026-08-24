// Copyright (c) 2026, UV Technolab and contributors

frappe.ui.form.on("Debug Session", {
	refresh(frm) {
		if (frm.doc.confidence) {
			frm.dashboard.set_headline(
				`Confidence: <b>${frm.doc.confidence}</b> &nbsp;•&nbsp; ${frappe.utils.escape_html(
					frm.doc.application || ""
				)} (${frappe.utils.escape_html(frm.doc.application_type || "Unknown")})`
			);
		}

		if (frm.doc.original_traceback) {
			frm.add_custom_button(__("Re-analyze (current source)"), () => {
				frappe.dom.freeze(__("Re-analyzing…"));
				frm.call("reanalyze")
					.then((r) => {
						frappe.dom.unfreeze();
						frm.reload_doc();
						const m = r.message || {};
						frappe.show_alert({
							message: __("Re-analyzed. Confidence: {0}", [m.confidence || "?"]),
							indicator: m.source_stale ? "orange" : "green",
						});
					})
					.catch(() => frappe.dom.unfreeze());
			});
		}

		if (frm.doc.file_path && frm.doc.line_number) {
			frm.add_custom_button(__("View Source"), () =>
				roottrace_view_source({ file_path: frm.doc.file_path, line_number: frm.doc.line_number })
			);
		}
	},
});
