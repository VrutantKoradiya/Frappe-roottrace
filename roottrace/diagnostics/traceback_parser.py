"""Deterministic Python/JS traceback parser. No AI, no guessing.

Handles the two shapes Frappe emits:
  - "Traceback (most recent call last):"        (plain)
  - "Traceback with variables (most recent call last):"  (frappe.get_traceback with locals)

For each frame it captures the source line Python prints under the `File` line and,
for variable tracebacks, the local variables. That embedded source line is what lets
RootTrace reason about a failure even when the file no longer lives on this bench.
"""

import re

FILE_RE = re.compile(r'^(?P<indent>\s*)File "(?P<file>.+?)", line (?P<line>\d+), in (?P<func>.+?)\s*$')
# `at func (file:line:col)` or `at file:line:col`  -- JavaScript stack frames
JS_FRAME_RE = re.compile(r'^\s*at\s+(?:(?P<func>[^\s(]+)\s+\()?(?P<file>[^\s()]+?):(?P<line>\d+):(?P<col>\d+)\)?\s*$')
PY_HEADER = "Traceback (most recent call last):"
PY_HEADER_VARS = "Traceback with variables (most recent call last):"
# a bare exception line, e.g. `frappe.exceptions.PermissionError` or `builtins.TypeError: msg`
EXC_RE = re.compile(r'^(?P<full>[A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit|Interrupt|Interupt))(?::[ ]?(?P<msg>.*))?$')
LOCAL_RE = re.compile(r'^\s+[A-Za-z_][\w.]*\s*=\s*.*$')

BUILTIN_EXCEPTIONS = {
	"TypeError", "AttributeError", "NameError", "KeyError", "ValueError",
	"IndexError", "ImportError", "ModuleNotFoundError", "ZeroDivisionError",
	"RuntimeError", "StopIteration", "AssertionError", "NotImplementedError",
	"FileNotFoundError", "OSError", "IOError", "RecursionError", "OverflowError",
	"UnboundLocalError", "ArithmeticError", "LookupError",
}
JS_EXCEPTIONS = {"TypeError", "ReferenceError", "SyntaxError", "RangeError", "Error", "EvalError", "URIError"}


def _indent(s):
	return len(s) - len(s.lstrip(" "))


def _split_blocks(text):
	"""Split into traceback blocks. Chained tracebacks keep the LAST block
	(the final re-raise), which is the exception that actually surfaced."""
	lines = text.splitlines()
	starts = [i for i, ln in enumerate(lines) if ln.strip() in (PY_HEADER, PY_HEADER_VARS)]
	if not starts:
		return lines, False  # no header (bare frames or JS) -- parse whole thing
	last = starts[-1]
	with_vars = lines[last].strip() == PY_HEADER_VARS
	return lines[last + 1:], with_vars


def _parse_exception(lines, from_idx):
	"""Find the exception type + message after the frames. Supports multi-line messages."""
	for i in range(from_idx, len(lines)):
		ln = lines[i]
		if not ln.strip():
			continue
		if _indent(ln) != 0:
			continue
		m = EXC_RE.match(ln.strip())
		if not m:
			continue
		full = m.group("full")
		short = full.split(".")[-1]
		msg_parts = [m.group("msg") or ""]
		# join continuation lines (a message that wrapped onto later lines)
		for j in range(i + 1, len(lines)):
			nxt = lines[j]
			if not nxt.strip():
				break
			if FILE_RE.match(nxt) or nxt.strip() in (PY_HEADER, PY_HEADER_VARS):
				break
			msg_parts.append(nxt.strip())
		return short, full, "\n".join(p for p in msg_parts if p).strip()
	return None, None, ""


def _parse_python(lines, with_vars):
	frames = []
	i, n = 0, len(lines)
	last_frame_end = 0
	while i < n:
		m = FILE_RE.match(lines[i])
		if not m:
			i += 1
			continue
		frame = {
			"file": m.group("file"),
			"line": int(m.group("line")),
			"func": m.group("func"),
			"code": "",
			"locals": [],
		}
		file_indent = _indent(lines[i])
		i += 1
		# source line printed under `File ...` (always the first deeper-indented line)
		if i < n and lines[i].strip() and _indent(lines[i]) > file_indent and not FILE_RE.match(lines[i]):
			code_indent = _indent(lines[i])
			frame["code"] = lines[i].strip()
			i += 1
			# locals: lines indented deeper than the code line (variable tracebacks only)
			while i < n and lines[i].strip() and _indent(lines[i]) > code_indent and not FILE_RE.match(lines[i]):
				if LOCAL_RE.match(lines[i]):
					frame["locals"].append(lines[i].strip())
				i += 1
		frames.append(frame)
		last_frame_end = i
	exc_short, exc_full, exc_msg = _parse_exception(lines, last_frame_end)
	return frames, exc_short, exc_full, exc_msg


def _parse_js(lines):
	frames, exc_short, exc_msg = [], None, ""
	for ln in lines:
		jm = JS_FRAME_RE.match(ln)
		if jm:
			frames.append({
				"file": jm.group("file"),
				"line": int(jm.group("line")),
				"func": jm.group("func") or "<anonymous>",
				"code": "",
				"locals": [],
			})
			continue
		s = ln.strip()
		if not s or s.startswith("at "):
			continue
		# first non-frame line that names a JS error type is the message
		if exc_short is None:
			mm = re.match(r'^(?P<type>[A-Za-z]+Error|Error):?\s*(?P<msg>.*)$', s)
			if mm and mm.group("type") in JS_EXCEPTIONS:
				exc_short, exc_msg = mm.group("type"), mm.group("msg").strip()
			elif "Cannot read propert" in s or "is not defined" in s or "is not a function" in s:
				exc_short, exc_msg = "TypeError", s
	return frames, exc_short, exc_short, exc_msg


def looks_like_js(text):
	return bool(re.search(r'^\s*at\s+\S+.*:\d+:\d+', text, re.M)) or "Cannot read propert" in text


def parse(text):
	"""Return a dict: {language, frames[], exc_type, exc_full, exc_message}.

	frames are ordered outermost-first, innermost (raise site) last -- the order
	Python prints them.
	"""
	text = (text or "").strip()
	if not text:
		return {"language": "unknown", "frames": [], "exc_type": None, "exc_full": None, "exc_message": ""}

	if looks_like_js(text) and not FILE_RE.search(text):
		frames, exc_short, exc_full, exc_msg = _parse_js(text.splitlines())
		lang = "javascript"
	else:
		lines, with_vars = _split_blocks(text)
		frames, exc_short, exc_full, exc_msg = _parse_python(lines, with_vars)
		lang = "python"
		# a JS error pasted with no `at` frames but a `TypeError: ...` line
		if not frames and not exc_short and looks_like_js(text):
			frames, exc_short, exc_full, exc_msg = _parse_js(text.splitlines())
			lang = "javascript"

	return {
		"language": lang,
		"frames": frames,
		"exc_type": exc_short,
		"exc_full": exc_full,
		"exc_message": exc_msg,
	}
