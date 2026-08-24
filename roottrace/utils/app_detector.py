"""Map a traceback file path to the app that owns it and classify it.

Classification is driven by the apps actually installed on THIS bench
(frappe.get_installed_apps()) -- nothing is hardcoded. An app named in a
traceback that is not installed here is still recognised as a bench-style
`apps/<name>/` path (Custom App), but flagged installed=False so the source
reader knows its files will not be present.
"""

import re
import frappe

APP_TYPE_FRAPPE = "Frappe"
APP_TYPE_ERPNEXT = "ERPNext"
APP_TYPE_CUSTOM = "Custom App"
APP_TYPE_THIRD_PARTY = "Third Party App"
APP_TYPE_UNKNOWN = "Unknown"

# frames that are pure framework plumbing -- never the actionable source
_DISPATCH_FILES = {
	"frappe/app.py", "frappe/api/__init__.py", "frappe/api/v1.py", "frappe/api/v2.py",
	"frappe/handler.py", "frappe/utils/typing_validations.py",
}
_DISPATCH_FUNCS = {"application", "handle", "handle_rpc_call", "execute_cmd", "call", "wrapper", "runserver"}
# the generic raise helpers frappe funnels every frappe.throw through
_RAISE_FILES = {"frappe/__init__.py"}
_RAISE_FUNCS = {"throw", "msgprint", "_raise_exception"}


def get_installed_apps():
	try:
		return list(frappe.get_installed_apps())
	except Exception:
		# outside a request/site context, fall back to apps.txt via bench
		try:
			return frappe.get_all_apps(with_internal_apps=True)
		except Exception:
			return ["frappe"]


def app_name_from_path(path):
	"""Extract the owning app from a traceback path.

	`apps/sigzensfa/sigzensfa/api/x.py` -> `sigzensfa`
	`.../site-packages/requests/api.py` -> `requests`
	"""
	if not path:
		return None
	norm = path.replace("\\", "/")
	parts = norm.split("/")
	if "apps" in parts:
		idx = parts.index("apps")
		if idx + 1 < len(parts):
			return parts[idx + 1]
	for marker in ("site-packages", "dist-packages"):
		if marker in parts:
			idx = parts.index(marker)
			if idx + 1 < len(parts):
				return parts[idx + 1]
	if "python3" in norm or norm.startswith("/usr/lib/python") or "/lib/python" in norm:
		return parts[-1].replace(".py", "") if parts else None
	# relative bench path without `apps/` prefix: first segment is the app
	return parts[0] if parts and parts[0] else None


def classify(path, installed=None):
	"""Return (app_name, app_type, installed_here: bool)."""
	if installed is None:
		installed = get_installed_apps()
	norm = (path or "").replace("\\", "/")
	app = app_name_from_path(norm)

	if "/site-packages/" in norm or "/dist-packages/" in norm:
		return app, APP_TYPE_THIRD_PARTY, False
	if norm.startswith("/usr/lib/python") or re.search(r"/python3\.\d+/", norm) and "apps/" not in norm:
		return app, APP_TYPE_THIRD_PARTY, False

	if app == "frappe":
		return app, APP_TYPE_FRAPPE, "frappe" in installed
	if app == "erpnext":
		return app, APP_TYPE_ERPNEXT, "erpnext" in installed
	if app and app in installed:
		return app, APP_TYPE_CUSTOM, True
	if "apps/" in norm or (app and not norm.startswith("/")):
		# clearly a bench app path, just not installed on this bench
		return app, APP_TYPE_CUSTOM, False
	return app, APP_TYPE_UNKNOWN, False


def _rel_after_app(path):
	norm = (path or "").replace("\\", "/")
	parts = norm.split("/")
	if "apps" in parts:
		idx = parts.index("apps")
		return "/".join(parts[idx + 2:]) if idx + 2 < len(parts) else norm
	return norm


def annotate_frames(frames, installed=None):
	"""Attach app / app_type / installed / role flags to every parsed frame."""
	if installed is None:
		installed = get_installed_apps()
	for f in frames:
		app, app_type, inst = classify(f["file"], installed)
		f["app"] = app
		f["app_type"] = app_type
		f["installed"] = inst
		f["rel"] = _rel_after_app(f["file"])
		norm = f["file"].replace("\\", "/")
		f["is_dispatch"] = (
			any(norm.endswith(d) for d in _DISPATCH_FILES) and f["func"] in _DISPATCH_FUNCS
		)
		f["is_raise_helper"] = (
			any(norm.endswith(r) for r in _RAISE_FILES) and f["func"] in _RAISE_FUNCS
		)
	return frames


def pick_actionable(frames):
	"""The most actionable frame: the one a developer should open first.

	Preference order:
	  1. deepest Custom App frame (the developer's own code)
	  2. deepest frame that is neither dispatch plumbing nor a raise helper
	  3. the raise site (last frame) as a last resort
	"""
	if not frames:
		return None
	customs = [f for f in frames if f.get("app_type") == APP_TYPE_CUSTOM]
	if customs:
		return customs[-1]
	meaningful = [f for f in frames if not f.get("is_raise_helper") and not f.get("is_dispatch")]
	if meaningful:
		return meaningful[-1]
	return frames[-1]


def pick_trigger(frames):
	"""The outermost frame that initiated the operation (entry point in real code)."""
	if not frames:
		return None
	customs = [f for f in frames if f.get("app_type") == APP_TYPE_CUSTOM]
	if customs:
		return customs[0]
	meaningful = [f for f in frames if not f.get("is_dispatch") and not f.get("is_raise_helper")]
	if meaningful:
		return meaningful[0]
	return frames[0]
