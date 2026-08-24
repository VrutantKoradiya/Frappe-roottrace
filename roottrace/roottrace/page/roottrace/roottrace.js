// RootTrace manual analysis page: paste a traceback -> diagnose -> create Debug Session.
frappe.pages["roottrace"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "RootTrace — Trace the error. Find the root.",
		single_column: true,
	});

	const $c = $(page.body);
	$c.html(`
		<div style="max-width:900px;margin:0 auto">
			<p class="text-muted">Paste a Python or JavaScript traceback / error and analyze it.
			Nothing is saved until you create a Debug Session.</p>
			<textarea class="form-control rt-input" rows="12"
				style="font-family:monospace;font-size:12.5px"
				placeholder="Traceback (most recent call last): ..."></textarea>
			<div style="margin:12px 0">
				<button class="btn btn-primary btn-sm rt-analyze">${__("Analyze Error")}</button>
				<button class="btn btn-default btn-sm rt-clear">${__("Clear")}</button>
			</div>
			<div class="rt-result"></div>
		</div>
	`);

	const $input = $c.find(".rt-input");
	const $result = $c.find(".rt-result");
	let last = null;

	$c.find(".rt-clear").on("click", () => {
		$input.val("");
		$result.empty();
		last = null;
	});

	$c.find(".rt-analyze").on("click", () => {
		const text = ($input.val() || "").trim();
		if (!text) {
			frappe.show_alert({ message: __("Paste a traceback first."), indicator: "orange" });
			return;
		}
		frappe.dom.freeze(__("Analyzing…"));
		frappe
			.call("roottrace.api.analyze.analyze_text", { traceback_text: text })
			.then((res) => {
				frappe.dom.unfreeze();
				last = res.message;
				render(last);
			})
			.catch(() => frappe.dom.unfreeze());
	});

	function render(r) {
		$result.empty();
		const $card = $(`<div class="frappe-card" style="padding:16px;margin-top:8px"></div>`);
		$card.html(roottrace.render_diagnosis(r));
		if (r && r.ok) {
			const $actions = $(`<div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap"></div>`);
			$(`<button class="btn btn-primary btn-sm">${__("Create Debug Session")}</button>`)
				.appendTo($actions)
				.on("click", () => {
					frappe.call("roottrace.api.session.create_debug_session", {
						result: JSON.stringify(r),
					}).then((res) => {
						if (res.message && res.message.name)
							frappe.set_route("Form", "Debug Session", res.message.name);
					});
				});
			$(`<button class="btn btn-default btn-sm">${__("View Original Traceback")}</button>`)
				.appendTo($actions)
				.on("click", () =>
					frappe.msgprint({
						title: __("Original Traceback"),
						message: `<pre style="white-space:pre-wrap;font-size:12px">${roottrace.esc(
							r.original_traceback
						)}</pre>`,
						wide: true,
					})
				);
			if (r.source_available && r.file_path) {
				$(`<button class="btn btn-default btn-sm">${__("View Source")}</button>`)
					.appendTo($actions)
					.on("click", () => roottrace_view_source(r));
			}
			$card.append($actions);
		}
		$result.append($card);
	}
};
