# Copyright (c) 2026, UV Technolab and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import escape_html

from roottrace.diagnostics import engine
from roottrace.utils import version

# engine keys that hold pre-formatted plain text destined for Text Editor (HTML) fields
_RICH_FIELDS = ("root_cause", "diagnosis", "call_chain", "related_frames", "suggestions")


def _pre(text):
	"""Preserve whitespace/arrows when a plain-text block lands in a Text Editor field."""
	if not text:
		return ""
	return f'<pre style="white-space:pre-wrap;word-break:break-word;font-family:inherit;margin:0">{escape_html(text)}</pre>'


def apply_result(doc, result):
	"""Copy an engine.analyze() result onto a Debug Session document."""
	if not result.get("ok"):
		frappe.throw(result.get("error", "Analysis failed."))

	doc.error_type = result.get("error_type")
	doc.error_message = result.get("error_message")
	doc.application = result.get("application")
	doc.application_type = result.get("application_type")
	doc.file_path = result.get("file_path")
	doc.line_number = result.get("line_number") or 0
	doc.function_name = result.get("function_name")
	doc.failure_location = result.get("failure_location")
	doc.failure_code = result.get("failure_code")
	doc.root_cause_location = result.get("root_cause_location")
	doc.original_traceback = result.get("original_traceback")
	doc.confidence = result.get("confidence")

	for key in _RICH_FIELDS:
		doc.set(key, _pre(result.get(key)))

	if not doc.site:
		doc.site = version.current_site()
	if not doc.frappe_version:
		doc.frappe_version = version.frappe_version()
	if not doc.erpnext_version:
		doc.erpnext_version = version.erpnext_version()
	if not doc.title:
		doc.title = result.get("title") or "Debug Session"
	doc.status = "Diagnosed"
	return doc


class DebugSession(Document):
	@frappe.whitelist()
	def reanalyze(self):
		"""Re-run diagnosis against the CURRENT bench source (for historical errors)."""
		if not self.original_traceback:
			frappe.throw("No original traceback stored to re-analyze.")
		result = engine.analyze(self.original_traceback)
		apply_result(self, result)
		self.save()
		return {"confidence": self.confidence, "source_stale": result.get("source_stale")}
