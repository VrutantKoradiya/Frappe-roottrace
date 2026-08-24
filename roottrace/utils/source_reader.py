"""Read the actual source around a failure line, from the current bench.

Never invents source. If the file is not on this bench, says so. Because
RootTrace may analyse historical errors, it always warns that the current
source is not guaranteed to match the code that failed, and escalates that
warning when the file was clearly modified after the error occurred.
"""

import os
import re
import frappe

CONTEXT = 7  # lines shown either side of the failure line

# key = value / "key": value patterns whose value must be masked before display/storage
_SECRET_KEYS = r"(?:password|passwd|pwd|secret|api[_-]?key|apikey|token|access[_-]?key|private[_-]?key|authorization|auth[_-]?token|client[_-]?secret|db[_-]?password)"
_SECRET_PATTERNS = [
	re.compile(rf'(["\']?{_SECRET_KEYS}["\']?\s*[:=]\s*)(["\'])(?P<v>[^"\']+)(\2)', re.I),
	re.compile(r'(Bearer\s+)(?P<v>[A-Za-z0-9._\-]{8,})', re.I),
	re.compile(r'\b(sk-[A-Za-z0-9]{8,})\b'),  # common secret-key prefix
	re.compile(r'(mysql|postgres|postgresql|redis|mongodb)(://[^:@\s]+:)(?P<v>[^@\s]+)(@)', re.I),
]


def mask_secrets(text):
	if not text:
		return text
	out = text
	for pat in _SECRET_PATTERNS:
		if "v" in pat.groupindex:
			out = pat.sub(lambda m: m.group(0).replace(m.group("v"), "***MASKED***"), out)
		else:
			out = pat.sub("***MASKED***", out)
	return out


def bench_path():
	# apps/frappe/frappe/utils -> up to bench root
	return os.path.abspath(os.path.join(frappe.get_app_path("frappe"), "..", "..", ".."))


def resolve(path):
	"""Turn a traceback path into an absolute path on this bench, or None."""
	if not path:
		return None
	norm = path.replace("\\", "/")
	if os.path.isabs(norm) and os.path.exists(norm):
		return norm
	root = bench_path()
	# traceback paths are usually bench-relative: `apps/<app>/...`
	cand = os.path.join(root, norm)
	if os.path.exists(cand):
		return cand
	if "apps/" in norm:
		cand = os.path.join(root, norm[norm.index("apps/"):])
		if os.path.exists(cand):
			return cand
	return None


def read_context(path, line, error_timestamp=None, context=CONTEXT):
	"""Return the source window around `line`.

	{available, path, abs_path, not_found, stale, warning, start, error_line, lines:[{no,text,is_error}]}
	"""
	abspath = resolve(path)
	result = {
		"available": False,
		"path": path,
		"abs_path": abspath,
		"not_found": abspath is None,
		"stale": False,
		"warning": "",
		"start": 0,
		"error_line": line,
		"lines": [],
	}
	if not abspath:
		result["warning"] = "Source file not found on the current bench."
		return result

	try:
		with open(abspath, "r", encoding="utf-8", errors="replace") as fh:
			src = fh.read().splitlines()
	except Exception as e:
		result["warning"] = f"Could not read source file: {e}"
		result["not_found"] = True
		return result

	total = len(src)
	if line < 1 or line > total:
		result["warning"] = f"Line {line} is out of range (file has {total} lines) -- the source has likely changed since this error."
		result["stale"] = True
		return result

	start = max(1, line - context)
	end = min(total, line + context)
	result["available"] = True
	result["start"] = start
	for no in range(start, end + 1):
		result["lines"].append({"no": no, "text": mask_secrets(src[no - 1]), "is_error": no == line})

	# staleness: compare file mtime against when the error happened
	try:
		mtime = os.path.getmtime(abspath)
	except Exception:
		mtime = None
	warn = ("The source shown is the CURRENT code on this bench, not a snapshot from when the "
			"error occurred. It may have changed.")
	if error_timestamp and mtime:
		ets = frappe.utils.get_datetime(error_timestamp).timestamp()
		if mtime > ets + 1:
			result["stale"] = True
			warn = ("WARNING: this source file was modified AFTER the error occurred "
					f"(file mtime is later than the error time). The line numbers and code "
					"below may not match the code that actually failed.")
	result["warning"] = warn
	return result
