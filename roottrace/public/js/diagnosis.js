// RootTrace shared diagnosis renderer. Loaded on desk via app_include_js so both
// the Error Log dialog and the RootTrace page render results identically.
frappe.provide("roottrace");

roottrace.esc = function (s) {
	return frappe.utils.escape_html(s == null ? "" : String(s));
};

roottrace.CONF_COLOR = { High: "green", Medium: "orange", Low: "red" };

// Build the diagnostic result HTML from an analyze_* result object.
roottrace.render_diagnosis = function (r) {
	if (!r || !r.ok) {
		return `<div class="text-danger" style="padding:12px">${roottrace.esc(
			(r && r.error) || "Could not analyse the input."
		)}</div>`;
	}
	const esc = roottrace.esc;
	const row = (icon, label, body) => `
		<div style="margin:14px 0">
			<div style="font-size:11px;letter-spacing:.06em;color:var(--text-muted);text-transform:uppercase">${icon} ${label}</div>
			<div style="margin-top:4px">${body}</div>
		</div>`;
	const pre = (t) =>
		`<pre style="white-space:pre-wrap;word-break:break-word;background:var(--fg-color,#f4f5f6);padding:10px 12px;border-radius:6px;margin:0;font-size:12.5px">${esc(t)}</pre>`;

	let html = `<div class="roottrace-diagnosis" style="font-size:13px">`;

	// error header
	html += `<div style="display:flex;align-items:center;gap:8px">
		<span style="font-size:16px">🔴</span>
		<strong style="font-size:15px">${esc(r.error_type || "Error")}</strong>
		<span class="indicator-pill ${roottrace.CONF_COLOR[r.confidence] || "gray"}"
			style="margin-left:auto">Confidence: ${esc(r.confidence || "Low")}</span>
	</div>`;
	if (r.error_message) html += `<div style="margin-top:6px;color:var(--text-color)">${esc(r.error_message)}</div>`;

	if (r.source_stale) {
		html += `<div class="alert alert-warning" style="margin-top:12px;font-size:12px">⚠️ ${esc(
			r.source_warning || "The source may have changed since this error occurred."
		)}</div>`;
	}

	html += row("📦", "Application",
		`<strong>${esc(r.application || "—")}</strong> <span class="text-muted">(${esc(r.application_type || "Unknown")})</span>`);

	html += row("📍", "Failure Location",
		`<div style="font-family:monospace">${esc(r.failure_location || "—")}</div>
		 <div class="text-muted" style="margin-top:2px">Function: <code>${esc(r.function_name || "—")}</code></div>
		 ${r.file_path ? `<div class="text-muted" style="font-size:11.5px">${esc(r.file_path)}</div>` : ""}`);

	if (r.failure_code) html += row("🧩", "Failing Code", pre(r.failure_code));
	if (!r.source_available && r.file_path)
		html += `<div class="text-muted" style="font-size:11.5px;margin:-6px 0 8px">Source file not on this bench — showing the line embedded in the traceback.</div>`;

	html += row("🎯", "Root Cause", `<div>${esc(r.root_cause)}</div>` +
		(r.root_cause_location ? `<div class="text-muted" style="margin-top:4px;font-family:monospace;font-size:11.5px">${esc(r.root_cause_location)}</div>` : ""));

	if (r.call_chain) html += row("🔗", "Call Chain", pre(r.call_chain));
	if (r.related_frames) html += row("🧵", "Related Frames", pre(r.related_frames));
	if (r.suggestions) html += row("💡", "What To Check", pre(r.suggestions));

	html += `</div>`;
	return html;
};
