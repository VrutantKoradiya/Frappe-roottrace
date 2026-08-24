# Copyright (c) 2026, UV Technolab and contributors

import frappe

from roottrace.diagnostics import engine
from roottrace.roottrace.doctype.debug_session.debug_session import apply_result

ROLE = "System Manager"


@frappe.whitelist()
def create_debug_session(result=None, traceback_text=None, error_log=None, title=None):
	"""Create a Debug Session from a prior analysis, a raw traceback, or an Error Log.

	Pass `result` (the JSON from analyze_*) to avoid re-analysing. Otherwise the
	traceback is analysed here.
	"""
	frappe.only_for(ROLE)

	if isinstance(result, str) and result.strip():
		result = frappe.parse_json(result)

	if not (result and result.get("ok")):
		if error_log:
			log = frappe.get_doc("Error Log", error_log)
			result = engine.analyze(log.error, error_timestamp=log.creation)
		elif (traceback_text or "").strip():
			result = engine.analyze(traceback_text)
		else:
			frappe.throw("Nothing to analyse: provide a result, a traceback, or an Error Log.")

	if not result.get("ok"):
		frappe.throw(result.get("error", "Analysis failed; cannot create a Debug Session."))

	doc = frappe.new_doc("Debug Session")
	doc.source = "Error Log" if error_log else "Manual"
	if error_log:
		doc.error_log = error_log
	if title:
		doc.title = title
	apply_result(doc, result)
	doc.insert()
	frappe.db.commit()
	return {"name": doc.name}
