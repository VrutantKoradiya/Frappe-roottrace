# Copyright (c) 2026, UV Technolab and contributors

import frappe

from roottrace.utils import source_reader

ROLE = "System Manager"


@frappe.whitelist()
def get_source(file_path, line_number, error_timestamp=None):
	"""Return masked source context around a failure line, from the current bench."""
	frappe.only_for(ROLE)
	return source_reader.read_context(file_path, int(line_number), error_timestamp)
