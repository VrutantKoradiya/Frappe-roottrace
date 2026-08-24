# Copyright (c) 2026, UV Technolab and contributors

import frappe

from roottrace.diagnostics import engine

ROLE = "System Manager"


def _guard():
	frappe.only_for(ROLE)


def _lean(result):
	# frames carry object refs used only server-side; keep the payload small for the UI
	result = dict(result)
	result.pop("frames", None)
	return result


@frappe.whitelist()
def analyze_text(traceback_text):
	"""Analyse a pasted traceback. Read-only; creates nothing."""
	_guard()
	if not (traceback_text or "").strip():
		frappe.throw("Paste a traceback to analyse.")
	return _lean(engine.analyze(traceback_text))


@frappe.whitelist()
def analyze_error_log(error_log):
	"""Analyse an existing Frappe Error Log (current or historical)."""
	_guard()
	log = frappe.get_doc("Error Log", error_log)
	result = engine.analyze(log.error, error_timestamp=log.creation)
	result["error_log"] = log.name
	result["error_log_method"] = log.method
	if result.get("ok") and not result.get("title"):
		result["title"] = (log.method or result.get("error_type") or "Error")[:140]
	return _lean(result)
