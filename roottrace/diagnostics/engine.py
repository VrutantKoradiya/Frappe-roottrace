"""Diagnostic orchestrator.

parse -> classify frames -> pick failure/trigger -> read real source -> apply
root-cause rule -> assemble a diagnosis. Deterministic; the only judgement lives
in rules.py and is always backed by traceback or source evidence.
"""

from roottrace.diagnostics import traceback_parser, rules
from roottrace.utils import app_detector, source_reader


def _short(path):
	norm = (path or "").replace("\\", "/")
	return "/".join(norm.split("/")[-2:]) if "/" in norm else norm


def _frame_loc(f):
	return f"{f.get('rel') or _short(f['file'])}:{f['line']}"


def _build_call_chain(trigger, actionable, frames, chain_tail):
	"""Developer-friendly vertical chain from the entry point to the exception."""
	steps = []
	seen = set()
	# walk meaningful frames from the trigger (entry point) down to the actionable frame
	started = trigger is None
	for f in frames:
		if trigger is not None and f is trigger:
			started = True
		if not started:
			continue
		if f.get("is_dispatch") or f.get("is_raise_helper"):
			continue
		label = f"{f['func']}()"
		if label not in seen:
			steps.append(label)
			seen.add(label)
		if actionable and f is actionable:
			break
	for t in (chain_tail or []):
		if t not in seen:
			steps.append(t)
			seen.add(t)
	return "\n    ↓\n".join(steps)


def _build_related_frames(frames, actionable, raise_frame):
	out = []
	for i, f in enumerate(frames, 1):
		marker = ""
		if f is actionable:
			marker = "   ← most actionable (failure location)"
		elif f is raise_frame and raise_frame is not actionable:
			marker = "   ← exception raised here"
		tag = f.get("app_type", "Unknown")
		out.append(f"{i}. [{tag}] {f.get('rel') or _short(f['file'])}:{f['line']} in {f['func']}{marker}")
	return "\n".join(out)


def _build_diagnosis(exc_type, exc_msg, actionable, raise_frame, trigger, rc, source):
	"""Full narrative: what/where/why + evidence + failure-vs-root-cause distinction."""
	L = []
	L.append(f"WHAT HAPPENED\n{exc_type}: {exc_msg or '(no message)'}")
	if actionable:
		L.append("WHERE (failure location)\n"
				 f"{actionable.get('rel') or actionable['file']}:{actionable['line']} "
				 f"in {actionable['func']}  [{actionable.get('app_type')}]")
	if raise_frame and raise_frame is not actionable:
		L.append("WHERE THE EXCEPTION WAS ACTUALLY RAISED\n"
				 f"{raise_frame.get('rel') or raise_frame['file']}:{raise_frame['line']} "
				 f"in {raise_frame['func']}  [{raise_frame.get('app_type')}]\n"
				 "This is framework plumbing -- the actionable code is the failure location above.")
	if trigger and trigger is not actionable:
		L.append("WHAT TRIGGERED IT (entry point)\n"
				 f"{trigger.get('rel') or trigger['file']}:{trigger['line']} in {trigger['func']}")
	L.append(f"WHY (root cause)\n{rc['root_cause']}")
	if rc.get("notes"):
		L.append("EVIDENCE / LIMITS\n- " + "\n- ".join(rc["notes"]))
	# failure-vs-root-cause distinction (spec §4)
	if raise_frame and raise_frame is not actionable:
		L.append("FAILURE LOCATION vs ROOT CAUSE\n"
				 "The exception surfaced inside framework code, but the actionable source and the "
				 "root cause are in the frame identified as the failure location above.")
	if source:
		if source.get("not_found"):
			L.append("SOURCE\nSource file not found on the current bench -- diagnosis is based on the "
					 "traceback (and any embedded code line) alone.")
		elif source.get("stale"):
			L.append("SOURCE WARNING\n" + source.get("warning", ""))
		elif source.get("available"):
			L.append("SOURCE\n" + source.get("warning", ""))
	return "\n\n".join(L)


def _build_failure_code(actionable, source):
	"""The ± context window if the file is on the bench; otherwise the single line
	Python embedded in the traceback; otherwise nothing."""
	if source and source.get("available"):
		lines = []
		for ln in source["lines"]:
			mark = " ←  ERROR" if ln["is_error"] else ""
			lines.append(f"{ln['no']:>5} | {ln['text']}{mark}")
		return "\n".join(lines)
	if actionable and actionable.get("code"):
		return (f"{actionable['line']:>5} | {source_reader.mask_secrets(actionable['code'])}   ←  ERROR"
				"\n(source file not on this bench; line shown is the one embedded in the traceback)")
	return ""


def _title(exc_type, actionable):
	base = exc_type or "Error"
	if actionable and actionable.get("func"):
		return f"{actionable['func']} {base}"
	return base


def analyze(traceback_text, error_timestamp=None, read_source=True):
	"""Analyse a raw traceback. Returns a diagnosis dict ready for UI / Debug Session."""
	parsed = traceback_parser.parse(traceback_text)
	frames = parsed["frames"]
	exc_type = parsed["exc_type"]
	exc_msg = parsed["exc_message"]

	if not frames and not exc_type:
		return {
			"ok": False,
			"error": "Could not parse a traceback from the input. Paste a full Python or JavaScript traceback.",
			"original_traceback": traceback_text,
		}

	installed = app_detector.get_installed_apps()
	app_detector.annotate_frames(frames, installed)

	actionable = app_detector.pick_actionable(frames)
	trigger = app_detector.pick_trigger(frames)
	raise_frame = frames[-1] if frames else None
	for f in frames:
		f["is_actionable"] = f is actionable
		f["is_raise"] = f is raise_frame
		f["is_trigger"] = f is trigger

	# read the real source at the actionable frame
	source = None
	if read_source and actionable:
		source = source_reader.read_context(actionable["file"], actionable["line"], error_timestamp)

	rc = rules.diagnose(parsed["language"], exc_type, exc_msg, actionable, frames)

	application = (actionable.get("app") if actionable else None) or ""
	application_type = (actionable.get("app_type") if actionable else None) or "Unknown"

	call_chain = _build_call_chain(trigger, actionable, frames, rc.get("chain_tail"))
	related = _build_related_frames(frames, actionable, raise_frame)
	diagnosis = _build_diagnosis(exc_type, exc_msg, actionable, raise_frame, trigger, rc, source)
	failure_code = _build_failure_code(actionable, source)

	return {
		"ok": True,
		"language": parsed["language"],
		"title": _title(exc_type, actionable),
		"error_type": exc_type,
		"error_message": source_reader.mask_secrets(exc_msg),
		"application": application,
		"application_type": application_type,
		"file_path": actionable["file"] if actionable else "",
		"line_number": actionable["line"] if actionable else 0,
		"function_name": actionable["func"] if actionable else "",
		"failure_location": _frame_loc(actionable) if actionable else "",
		"failure_code": failure_code,
		"root_cause": rc["root_cause"],
		"root_cause_location": rc.get("root_cause_location", ""),
		"diagnosis": diagnosis,
		"category": rc.get("category", "Unknown"),
		"call_chain": call_chain,
		"related_frames": related,
		"suggestions_list": rc.get("suggestions", []),
		"suggestions": "\n".join(f"{i}. {s}" for i, s in enumerate(rc.get("suggestions", []), 1)),
		"confidence": rc.get("confidence", "Low"),
		"source_available": bool(source and source.get("available")),
		"source_stale": bool(source and source.get("stale")),
		"source_warning": (source or {}).get("warning", ""),
		"original_traceback": traceback_text,
		"frames": frames,
	}
