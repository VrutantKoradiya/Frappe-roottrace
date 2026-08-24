"""Environment facts, read from the live bench (never hardcoded)."""

import frappe


def frappe_version():
	try:
		return frappe.__version__
	except Exception:
		return ""


def erpnext_version():
	try:
		import erpnext
		return erpnext.__version__
	except Exception:
		return ""


def app_version(app):
	try:
		return frappe.get_attr(f"{app}.__version__")
	except Exception:
		return ""


def current_site():
	return getattr(frappe.local, "site", "") or ""
