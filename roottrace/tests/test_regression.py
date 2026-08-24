# Copyright (c) 2026, UV Technolab and contributors
"""Regression suite driven by the 10 attached sample errors.

Each case asserts the ACTUAL expected diagnosis (type, failure location,
application, category, confidence, root cause) -- not merely "analysis ran".
The sample apps (sigzensfa / sfa_sigzen / sigzen_whatsapp) are not installed on
this bench, so source is legitimately unavailable; the engine must still
diagnose from the traceback (and its embedded code line) alone.
"""

import json
import frappe
from frappe.tests.utils import FrappeTestCase

from roottrace.diagnostics import engine
from roottrace.diagnostics import traceback_parser
from roottrace.api import analyze as analyze_api, session as session_api
from roottrace.tests.samples import SAMPLES

# expected diagnosis per sample number
EXPECT = {
	1: dict(error_type="TypeError", function_name="_parse_city_filter_value",
			file_ends="expence_claim_type/helpers.py", line=345,
			application="sigzensfa", application_type="Custom App",
			category="Python", confidence="Medium", rc=["None"]),
	2: dict(error_type="AuthenticationError", function_name="login",
			file_ends="domains/api/auth.py", line=90,
			application="sigzensfa", application_type="Custom App",
			category="Frappe", confidence="High", rc=["Authentication"]),
	3: dict(error_type="OutgoingEmailError", function_name="find_outgoing",
			file_ends="email_account/email_account.py", line=402,
			application="frappe", application_type="Frappe",
			category="Configuration", confidence="High", rc=["Email Account"],
			source_available=True),  # frappe frame -> the file IS on this bench
	4: dict(error_type="ValidationError", function_name="assert_prior_party_rows_have_type_of_activity",
			file_ends="doctype/field_activity/field_activity.py", line=53,
			application="sigzensfa", application_type="Custom App",
			category="Frappe", confidence="High", rc=["Type Of Activity"]),
	5: dict(error_type="TypeError", function_name="stock_report",
			file_ends="mobile_api/stock_report.py", line=47,
			application="sfa_sigzen", application_type="Custom App",
			category="Python", confidence="High", rc=['url_doc("base_url_stock")', "None"]),
	6: dict(error_type="ValidationError", function_name="create_doctype_data",
			file_ends="sigzen_whatsapp/install.py", line=91,
			application="sigzen_whatsapp", application_type="Custom App",
			category="Frappe", confidence="High", rc=["Select"]),
	7: dict(error_type="AttributeError", function_name="send_coupon_code",
			file_ends="events/event.py", line=516,
			application="sigzen_whatsapp", application_type="Custom App",
			category="Python", confidence="High",
			rc=["custom_whatsapp_verification_coupon_code", "WebPage"]),
	8: dict(error_type="DoesNotExistError", function_name="get_customer_list",
			file_ends="field_activity/tour_parties.py", line=28,
			application="sigzensfa", application_type="Custom App",
			category="Frappe", confidence="High", rc=["undefined", "JavaScript"]),
	9: dict(error_type="OutgoingEmailError", function_name="notify",
			file_ends="events/approval_notifications.py", line=42,
			application="sigzensfa", application_type="Custom App",
			category="Configuration", confidence="High", rc=["Email Account"]),
	10: dict(error_type="PermissionError", function_name="tour_type_list",
			 file_ends="domains/tour/lookups.py", line=117,
			 application="sigzensfa", application_type="Custom App",
			 category="Permission", confidence="Medium", rc=["Tour Type", "permission"]),
}


class TestRootTraceRegression(FrappeTestCase):
	def test_all_samples(self):
		for num, exp in EXPECT.items():
			with self.subTest(sample=num):
				r = engine.analyze(SAMPLES[num])
				self.assertTrue(r["ok"], f"#{num} did not parse")
				self.assertEqual(r["error_type"], exp["error_type"], f"#{num} error_type")
				self.assertEqual(r["function_name"], exp["function_name"], f"#{num} function")
				self.assertTrue(r["file_path"].endswith(exp["file_ends"]),
								f"#{num} file_path={r['file_path']}")
				self.assertEqual(r["line_number"], exp["line"], f"#{num} line")
				self.assertEqual(r["application"], exp["application"], f"#{num} application")
				self.assertEqual(r["application_type"], exp["application_type"], f"#{num} app_type")
				self.assertEqual(r["category"], exp["category"], f"#{num} category")
				self.assertEqual(r["confidence"], exp["confidence"], f"#{num} confidence")
				for token in exp["rc"]:
					self.assertIn(token.lower(), r["root_cause"].lower(),
								  f"#{num} root_cause missing {token!r}: {r['root_cause']!r}")
				# failing code must be present (embedded traceback line even without the file)
				self.assertTrue(r["failure_code"], f"#{num} no failing code")
				self.assertTrue(r["title"], f"#{num} no title")
				# sample apps aren't installed here -> no source; frappe/erpnext frames DO have source
				self.assertEqual(r["source_available"], exp.get("source_available", False),
								 f"#{num} source_available")

	def test_failure_vs_raise_distinction(self):
		# #3: exception raised in frappe __init__ but actionable frame is find_outgoing
		r = engine.analyze(SAMPLES[3])
		self.assertEqual(r["function_name"], "find_outgoing")
		self.assertIn("_raise_exception", r["related_frames"])
		self.assertIn("raised here", r["related_frames"])

	def test_call_chain_built(self):
		r = engine.analyze(SAMPLES[5])
		self.assertIn("stock_report", r["call_chain"])
		self.assertIn("TypeError", r["call_chain"])
		self.assertIn("↓", r["call_chain"])

	def test_secret_masking(self):
		tb = ('Traceback (most recent call last):\n'
			  '  File "apps/frappe/frappe/x.py", line 3, in go\n'
			  '    conn = connect(password="hunter2secret")\n'
			  'builtins.RuntimeError: boom password="hunter2secret"')
		r = engine.analyze(tb)
		self.assertNotIn("hunter2secret", r["failure_code"])
		self.assertNotIn("hunter2secret", r["error_message"])

	def test_javascript_error(self):
		js = ("TypeError: Cannot read properties of undefined (reading 'name')\n"
			  "    at render (app.bundle.js:120:15)\n"
			  "    at HTMLButtonElement.onclick (form.js:44:9)")
		r = engine.analyze(js)
		self.assertTrue(r["ok"])
		self.assertEqual(r["language"], "javascript")
		self.assertEqual(r["category"], "JavaScript")
		self.assertIn("name", r["root_cause"])

	def test_unparseable_input(self):
		r = engine.analyze("this is not a traceback at all")
		self.assertFalse(r["ok"])

	def test_create_debug_session_manual(self):
		r = analyze_api.analyze_text(SAMPLES[5])
		out = session_api.create_debug_session(result=json.dumps(r))
		doc = frappe.get_doc("Debug Session", out["name"])
		self.assertEqual(doc.source, "Manual")
		self.assertEqual(doc.error_type, "TypeError")
		self.assertEqual(doc.line_number, 47)
		self.assertEqual(doc.confidence, "High")
		self.assertIn("url_doc", doc.root_cause)  # stored (wrapped) root cause
		frappe.delete_doc("Debug Session", doc.name, force=True)

	def test_historical_error_log_flow(self):
		# Simulate: an old Error Log exists, RootTrace analyses it, creates a Debug Session.
		log = frappe.get_doc({
			"doctype": "Error Log",
			"method": "sfa_sigzen.mobile_api.stock_report.stock_report",
			"error": SAMPLES[5],
		}).insert(ignore_permissions=True)
		r = analyze_api.analyze_error_log(log.name)
		self.assertTrue(r["ok"])
		self.assertEqual(r["error_log"], log.name)
		out = session_api.create_debug_session(result=json.dumps(r), error_log=log.name)
		doc = frappe.get_doc("Debug Session", out["name"])
		self.assertEqual(doc.source, "Error Log")
		self.assertEqual(doc.error_log, log.name)
		self.assertEqual(doc.error_type, "TypeError")
		frappe.delete_doc("Debug Session", doc.name, force=True)
		frappe.delete_doc("Error Log", log.name, force=True)
