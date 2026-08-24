"""Evidence-based root-cause rules.

One function per exception family, dispatched on the exception type + message +
the actual failing source line (which Frappe embeds in the traceback). Each rule
returns only what the evidence supports and sets a confidence that reflects how
much of the conclusion is proven vs inferred. Nothing here fabricates a cause.

Consolidated into a single module on purpose (spec: no unnecessary files).
Categories map to the spec's python/frappe/permissions/database/api/configuration
diagnostic areas.
"""

import re

HIGH, MEDIUM, LOW = "High", "Medium", "Low"

_DOC_CALL_RE = re.compile(
	r'(?:get_doc|get_list|get_all|get_value|get_cached_doc|get_single|exists|get_meta|delete_doc)'
	r'\(\s*["\'](?P<dt>[^"\']+)["\']'
)


def _doctype_in_frames(frames):
	"""First DocType named in any frame's code line (e.g. get_list("Tour Type"))."""
	for f in frames:
		m = _DOC_CALL_RE.search(f.get("code") or "")
		if m:
			return m.group("dt")
	return None


def _none_plus_str_expr(code):
	"""In `a(...) + "x"` return `a(...)` -- the operand that produced None."""
	if not code:
		return None
	m = re.search(r'([A-Za-z_][\w.]*\([^()]*\))\s*\+\s*["\']', code)
	if m:
		return m.group(1)
	m = re.search(r'([A-Za-z_][\w.]*)\s*\+\s*["\']', code)
	return m.group(1) if m else None


def _first_call(code):
	"""First `name(...)` or `obj.attr(...)` being invoked on a line."""
	if not code:
		return None
	m = re.search(r'([A-Za-z_][\w.]*)\s*\(', code.split("=", 1)[-1])
	return m.group(1) if m else None


def _loc(frame):
	if not frame:
		return ""
	return f"{frame.get('rel') or frame.get('file')}:{frame.get('line')} in {frame.get('func')}"


# ---------------------------------------------------------------- python ----

def _type_error(exc_msg, actionable, frames):
	code = actionable.get("code") if actionable else ""
	if "unsupported operand type(s) for +" in exc_msg and "NoneType" in exc_msg:
		expr = _none_plus_str_expr(code)
		if expr:
			rc = (f"`{expr}` returned None. The code then tried to concatenate that None "
				  f"with a string, which Python rejects.")
			chain_tail = [expr, "None", "None + string", "TypeError"]
		else:
			rc = ("A value on the left of `+` was None while the right side was a string. "
				  "None cannot be concatenated with str.")
			chain_tail = ["None", "None + string", "TypeError"]
		return {
			"category": "Python",
			"root_cause": rc,
			"root_cause_location": _loc(actionable),
			"suggestions": [
				f"Check why {expr or 'the left operand'} is None -- often a missing/empty configuration value or a lookup that found nothing.",
				"Add a guard/default before concatenating (e.g. `value = get(...) or ''` or raise a clear error if it is missing).",
				"Verify the current site's configuration provides the expected value.",
			],
			"confidence": HIGH if code else MEDIUM,
			"chain_tail": chain_tail,
			"notes": ["The failing line and operand types are proven by the traceback."],
		}
	if "not callable" in exc_msg and "NoneType" in exc_msg:
		callee = _first_call(code)
		rc = (f"`{callee}` is None, so calling it raised 'NoneType is not callable'. "
			  if callee else "Something being called is None. ")
		rc += ("The most common cause is accessing a method/attribute on a frappe._dict "
			   "(it returns None for missing keys) or on an object that does not define it.")
		return {
			"category": "Python",
			"root_cause": rc,
			"root_cause_location": _loc(actionable),
			"suggestions": [
				f"Confirm that {callee or 'the called object'} is what you expect -- if it comes from frappe.form_dict / a _dict, a missing key yields None.",
				"For request form data use `frappe.request.form` / a MultiDict for `.getlist`, or guard with `if callable(x)`.",
				"Inspect the source to confirm the attribute is actually defined on that object.",
			],
			"confidence": MEDIUM,
			"chain_tail": [f"{callee}()" if callee else "call", "None()", "TypeError"],
			"notes": ["'not callable' is proven; the exact object requires the source to confirm."],
		}
	return {
		"category": "Python",
		"root_cause": f"A TypeError occurred: {exc_msg}",
		"root_cause_location": _loc(actionable),
		"suggestions": ["Inspect the failing line and the types of the operands/arguments involved."],
		"confidence": MEDIUM if actionable and actionable.get("code") else LOW,
		"chain_tail": ["TypeError"],
		"notes": [],
	}


def _attribute_error(exc_msg, actionable, frames):
	m = re.search(r"'([^']+)' object has no attribute '([^']+)'", exc_msg)
	obj, attr = (m.group(1), m.group(2)) if m else (None, None)
	rc = f"Attribute `{attr}` does not exist on a `{obj}` object." if attr else f"AttributeError: {exc_msg}"
	suggestions = []
	if attr and attr.startswith("custom_"):
		rc += (f" `{attr}` looks like a Custom Field. It is likely missing on the `{obj}` "
			   "DocType, or this document is not the DocType you assumed.")
		suggestions = [
			f"Verify a Custom Field `{attr}` exists on `{obj}` (Customize Form / Custom Field list).",
			f"Confirm the document really is a `{obj}` and carries that field before accessing it.",
			f"Guard with `doc.get('{attr}')` instead of attribute access if the field is optional.",
		]
		confidence = HIGH
	else:
		suggestions = [
			f"Check the object is really a `{obj}` and that `{attr}` is spelled correctly / defined.",
			f"Use `.get('{attr}')` or `getattr(obj, '{attr}', None)` when the attribute may be absent.",
		]
		confidence = HIGH if attr else MEDIUM
	return {
		"category": "Python",
		"root_cause": rc,
		"root_cause_location": _loc(actionable),
		"suggestions": suggestions,
		"confidence": confidence,
		"chain_tail": [f".{attr}" if attr else "attribute access", "AttributeError"],
		"notes": ["The missing attribute and object type are stated by the exception itself.",
				  "Whether the Custom Field exists requires checking DocType metadata."],
	}


def _key_error(exc_msg, actionable, frames):
	key = exc_msg.strip().strip("'\"")
	return {
		"category": "Python",
		"root_cause": f"Key {exc_msg} was not present in the dict/mapping being indexed.",
		"root_cause_location": _loc(actionable),
		"suggestions": [
			f"Use `.get({key!r})` instead of `[{key!r}]` if the key may be absent.",
			"Check upstream where this mapping is built -- the expected key may never be set.",
		],
		"confidence": MEDIUM,
		"chain_tail": [f"[{exc_msg}]", "KeyError"],
		"notes": [],
	}


def _name_error(exc_msg, actionable, frames):
	return {
		"category": "Python",
		"root_cause": f"{exc_msg}. A name is used before it is defined or imported.",
		"root_cause_location": _loc(actionable),
		"suggestions": ["Define/import the name before use; check for a typo or a missing import."],
		"confidence": HIGH,
		"chain_tail": ["NameError"],
		"notes": [],
	}


def _import_error(exc_msg, actionable, frames):
	return {
		"category": "Python",
		"root_cause": f"An import failed: {exc_msg}. The module/name is missing or not installed.",
		"root_cause_location": _loc(actionable),
		"suggestions": [
			"Confirm the module is installed in this bench's environment and the import path is correct.",
			"If it is an app module, confirm the app is installed on this site.",
		],
		"confidence": HIGH,
		"chain_tail": ["ImportError"],
		"notes": [],
	}


# ---------------------------------------------------------------- frappe ----

def _outgoing_email(exc_msg, actionable, frames):
	return {
		"category": "Configuration",
		"root_cause": ("No default outgoing Email Account is configured for this site. Frappe tried "
					   "to send mail and found no account to send it through. This is a site "
					   "configuration issue, not a code bug."),
		"root_cause_location": "Site configuration: Email Account (default outgoing)",
		"suggestions": [
			"Create/enable an Email Account with 'Enable Outgoing' and mark it Default Outgoing (Settings > Email Account).",
			"If mail is expected to be off, wrap the sendmail call so it degrades gracefully when no account exists.",
			"Verify the correct site is targeted -- outgoing account config is per site.",
		],
		"confidence": HIGH,
		"chain_tail": ["find_outgoing()", "no default account", "OutgoingEmailError"],
		"notes": ["Proven by the exception message.",
				  "Confirming the fix requires inspecting this site's Email Account records."],
	}


def _validation_error(exc_msg, actionable, frames):
	# select-option validation raised deep in base_document
	raised_in = next((f for f in frames if f.get("func") == "_validate_selects"), None)
	if raised_in or ("cannot be" in exc_msg and "should be one of" in exc_msg):
		return {
			"category": "Frappe",
			"root_cause": ("A Select field was set to a value outside its allowed options. "
						   f"{exc_msg.strip()}"),
			"root_cause_location": _loc(actionable),
			"suggestions": [
				"Set the field to one of the exact allowed options (watch for case: 'document' vs 'Document').",
				"Fix the data source that produced the invalid value before saving.",
			],
			"confidence": HIGH,
			"chain_tail": ["invalid Select value", "ValidationError"],
			"notes": ["The allowed options are listed in the message itself."],
		}
	# a deliberate frappe.throw business rule from application code
	return {
		"category": "Frappe",
		"root_cause": ("A validation rule rejected the operation. This is an intentional check "
					   f"(frappe.throw), not a crash. Reason: {exc_msg.strip()}"),
		"root_cause_location": _loc(actionable),
		"suggestions": [
			"Satisfy the business rule stated in the message before retrying.",
			f"If the rule itself is wrong, review the validation at {_loc(actionable)}.",
		],
		"confidence": HIGH,
		"chain_tail": ["frappe.throw()", "ValidationError"],
		"notes": ["The message is the validation reason, raised deliberately by the throwing code."],
	}


def _permission_error(exc_msg, actionable, frames):
	dt = _doctype_in_frames(frames)
	is_read = any(f.get("func") in ("check_read_permission", "_set_permission_map", "get_list") for f in frames)
	target = f" on `{dt}`" if dt else ""
	rc = (f"The current user lacks permission{target}"
		  + (" (a read/list permission check failed)." if is_read else "."))
	return {
		"category": "Permission",
		"root_cause": rc,
		"root_cause_location": _loc(actionable),
		"suggestions": [
			f"Check the Role Permissions for {dt or 'this DocType'} and the roles of the calling user.",
			"Confirm the user is the one you expect (session / API key) -- Guest and API users often lack roles.",
			"If this call is intentionally system-level, pass `ignore_permissions=True` (only where safe).",
			"Check User Permissions / restrictions that could block this specific record.",
		],
		"confidence": MEDIUM,
		"chain_tail": [f"has_permission({dt})" if dt else "has_permission()", "denied", "PermissionError"],
		"notes": ["PermissionError carries no message; the DocType is inferred from the call chain.",
				  "Confirming the cause requires inspecting role permissions and the user's roles."],
	}


def _does_not_exist(exc_msg, actionable, frames):
	# frappe message is "{doctype} {name} not found"; doctype may contain spaces,
	# name is the last token -> greedy doctype + a single non-space name token.
	m = re.match(r"^(?P<dt>.+)\s+(?P<name>\S+)\s+not found$", exc_msg.strip())
	dt = m.group("dt") if m else _doctype_in_frames(frames)
	name = m.group("name") if m else None
	junk = {"undefined", "null", "none", "nan", ""}
	if name and name.lower() in junk:
		rc = (f"A `{dt}` was requested with the identifier '{name}'. That is not a real record id -- "
			  f"it is a JavaScript `undefined`/`null` that reached the server as the literal string '{name}'.")
		suggestions = [
			f"Fix the caller/frontend so a valid {dt} id is sent (the current value serialised a JS undefined).",
			f"Guard the endpoint: reject/short-circuit when the id is empty or '{name}' before calling get_doc.",
		]
		conf = HIGH
	else:
		rc = f"`{dt}` '{name}' does not exist." if name else f"A requested document does not exist: {exc_msg}"
		suggestions = [
			f"Confirm a {dt} named '{name}' exists on this site." if name else "Confirm the requested record exists.",
			"Check the id source -- it may be stale, from another site, or mistyped.",
		]
		conf = HIGH
	return {
		"category": "Frappe",
		"root_cause": rc,
		"root_cause_location": _loc(actionable),
		"suggestions": suggestions,
		"confidence": conf,
		"chain_tail": [f"get_doc({dt!r}, {name!r})" if dt else "get_doc(...)", "not found", "DoesNotExistError"],
		"notes": ["The DocType and missing id are taken from the exception message."],
	}


def _authentication_error(exc_msg, actionable, frames):
	msg = exc_msg.strip() or "Authentication failed."
	return {
		"category": "Frappe",
		"root_cause": (f"Authentication failed: {msg}. The supplied credentials were rejected. "
					   "This is expected behaviour for a bad login, not necessarily a code defect."),
		"root_cause_location": _loc(actionable),
		"suggestions": [
			"Verify the username/email and password are correct and the user is Enabled.",
			"Check the account is not locked and login is allowed for this user type.",
			"If this is an API/integration, confirm the credentials/keys it sends are valid.",
		],
		"confidence": HIGH,
		"chain_tail": ["authenticate()", "invalid credentials", "AuthenticationError"],
		"notes": ["An authentication failure is a data/credentials issue, not a traceback bug."],
	}


# ---------------------------------------------------------------- javascript ----

def _js_error(exc_type, exc_msg, actionable, frames):
	if "Cannot read propert" in exc_msg:
		pm = re.search(r"reading '([^']+)'", exc_msg)
		prop = pm.group(1) if pm else None
		rc = (f"Read of property `{prop}` on an undefined/null value." if prop
			  else "Property read on an undefined/null value.")
		suggestions = [
			f"Guard the access (`obj?.{prop}` or `if (obj) ...`) -- the object was undefined/null at that point." if prop
			else "Guard the access with an existence/optional-chaining check.",
			"Trace where the object should have been assigned; an async value or missing field is common.",
		]
	elif exc_type == "ReferenceError":
		rc = f"{exc_msg}. A variable is used before it is defined."
		suggestions = ["Define/import the identifier before use; check load order and typos."]
	elif exc_type == "SyntaxError":
		rc = f"JavaScript failed to parse: {exc_msg}."
		suggestions = ["Fix the syntax at the reported location; check for a missing bracket/quote."]
	else:
		rc = f"{exc_type}: {exc_msg}"
		suggestions = ["Inspect the reported frame and the value involved."]
	return {
		"category": "JavaScript",
		"root_cause": rc,
		"root_cause_location": _loc(actionable),
		"suggestions": suggestions,
		"confidence": MEDIUM,
		"chain_tail": [exc_type or "Error"],
		"notes": ["JavaScript coverage is best-effort in V1; source is client-side and not read from the bench."],
	}


# ---------------------------------------------------------------- dispatch ----

_PY_RULES = {
	"TypeError": _type_error,
	"AttributeError": _attribute_error,
	"KeyError": _key_error,
	"NameError": _name_error,
	"ImportError": _import_error,
	"ModuleNotFoundError": _import_error,
	"OutgoingEmailError": _outgoing_email,
	"ValidationError": _validation_error,
	"MandatoryError": _validation_error,
	"PermissionError": _permission_error,
	"DoesNotExistError": _does_not_exist,
	"AuthenticationError": _authentication_error,
}


def _generic(exc_type, exc_msg, actionable, frames):
	return {
		"category": "Unknown",
		"root_cause": (f"{exc_type or 'An error'} occurred"
					   + (f": {exc_msg}" if exc_msg else ".")
					   + " RootTrace does not have a specific rule for this exception; "
					   "the failure location and frames below are still reliable."),
		"root_cause_location": _loc(actionable),
		"suggestions": [
			"Open the failure location and inspect the failing line and its inputs.",
			"Check the message text for the specific condition that was violated.",
		],
		"confidence": LOW,
		"chain_tail": [exc_type or "Error"],
		"notes": ["No category-specific rule matched; conclusions are limited to the traceback facts."],
	}


def diagnose(language, exc_type, exc_msg, actionable, frames):
	"""Return the root-cause dict for a parsed error."""
	exc_msg = exc_msg or ""
	if language == "javascript":
		return _js_error(exc_type, exc_msg, actionable, frames)
	rule = _PY_RULES.get(exc_type)
	if rule:
		return rule(exc_msg, actionable, frames)
	return _generic(exc_type, exc_msg, actionable, frames)
