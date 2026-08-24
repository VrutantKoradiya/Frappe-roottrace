// Adds "Analyze with RootTrace" to the standard Error Log form (via doctype_js hook).
// Works on historical logs too -- it reads the stored traceback and inspects the
// current bench source, warning when that source may have changed.
frappe.ui.form.on("Error Log", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Analyze with RootTrace"), () => roottrace_analyze_log(frm));
	},
});

function roottrace_analyze_log(frm) {
	frappe.dom.freeze(__("RootTrace is analyzing…"));
	frappe
		.call("roottrace.api.analyze.analyze_error_log", { error_log: frm.doc.name })
		.then((res) => {
			frappe.dom.unfreeze();
			const r = res.message;
			if (!r || !r.ok) {
				frappe.msgprint({
					title: __("RootTrace"),
					message: (r && r.error) || __("Could not analyze this Error Log."),
					indicator: "red",
				});
				return;
			}
			roottrace_show_result(r, { error_log: frm.doc.name });
		})
		.catch(() => frappe.dom.unfreeze());
}

// Shared result dialog used by the Error Log button and the RootTrace page.
window.roottrace_show_result = function (r, opts) {
	opts = opts || {};
	const d = new frappe.ui.Dialog({
		title: __("RootTrace — {0}", [r.error_type || "Diagnosis"]),
		size: "large",
		primary_action_label: __("Create Debug Session"),
		primary_action() {
			frappe.call("roottrace.api.session.create_debug_session", {
				result: JSON.stringify(r),
				error_log: opts.error_log || null,
			}).then((res) => {
				d.hide();
				if (res.message && res.message.name) {
					frappe.set_route("Form", "Debug Session", res.message.name);
				}
			});
		},
	});
	d.$body.html(roottrace.render_diagnosis(r));

	// secondary actions
	d.add_custom_action(__("View Original Traceback"), () => {
		frappe.msgprint({
			title: __("Original Traceback"),
			message: `<pre style="white-space:pre-wrap;font-size:12px">${roottrace.esc(r.original_traceback)}</pre>`,
			wide: true,
		});
	});
	if (r.source_available && r.file_path) {
		d.add_custom_action(__("View Source"), () => roottrace_view_source(r));
	}
	d.show();
};

window.roottrace_view_source = function (r) {
	frappe.call("roottrace.api.source.get_source", {
		file_path: r.file_path,
		line_number: r.line_number,
	}).then((res) => {
		const s = res.message || {};
		let body = "";
		if (s.warning) body += `<div class="text-muted" style="margin-bottom:8px">${roottrace.esc(s.warning)}</div>`;
		if (s.available) {
			body += `<pre style="font-size:12px;line-height:1.5">${s.lines
				.map((l) => {
					const t = `${String(l.no).padStart(5)} | ${roottrace.esc(l.text)}`;
					return l.is_error
						? `<span style="background:#ffe0e0;display:block">${t}   ← ERROR</span>`
						: t;
				})
				.join("\n")}</pre>`;
		} else {
			body += `<div class="text-danger">${roottrace.esc(s.warning || "Source not available.")}</div>`;
		}
		frappe.msgprint({ title: __("Source: {0}", [r.file_path]), message: body, wide: true });
	});
};
