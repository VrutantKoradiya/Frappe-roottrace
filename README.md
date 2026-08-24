# RootTrace

**Trace the error. Find the root.**

A developer-focused debugging aid that sits on top of Frappe's existing Error Log.
It does not replace Error Log — it analyses a traceback and points at the most
*actionable* source of the problem: exact app, file, line, function, failing code,
call chain, likely root cause, what to check, and a confidence level.

## Install

```bash
bench get-app https://github.com/<your-github-username>/roottrace
bench --site <your-site> install-app roottrace
```

Requires Frappe v15+. ERPNext is optional.

## How to use

**1. From an existing Error Log (incl. historical ones)**
Open any Error Log → **Analyze with RootTrace** → review the diagnosis → **Create Debug Session**.
Works on errors created before RootTrace was installed; it inspects the *current* bench
source and warns when that source may have changed since the error occurred.

**2. Manual traceback**
Go to `/app/roottrace` → paste a Python or JavaScript traceback → **Analyze Error** →
**Create Debug Session**.

**3. Debug Session**
The single DocType that stores a diagnosis. Buttons: **Re-analyze (current source)**,
**View Source**.

## What it distinguishes

- **Failure location** — the actionable frame a developer should open first.
- **Raise site** — where the exception was technically raised (often framework plumbing).
- **Trigger** — the entry point that started the operation.
- **Root cause** — the value / config / state that actually caused it.

Example: a `PermissionError` raised inside `frappe.has_permission` is reported against the
*custom app frame* that called `get_list(...)`, not the frappe raise site.

## Architecture

```
roottrace/
  diagnostics/
    traceback_parser.py   # deterministic parser (Python + JS, incl. "with variables")
    rules.py              # evidence-based root-cause rules per exception family
    engine.py             # orchestrator: parse → classify → locate → read source → diagnose
  utils/
    app_detector.py       # frame → owning app + Frappe/ERPNext/Custom/Third-Party/Unknown
    source_reader.py       # read bench source, mask secrets, staleness warning
    version.py
  api/                    # whitelisted: analyze_text, analyze_error_log, get_source, create_debug_session
  roottrace/
    doctype/debug_session/
    page/roottrace/        # manual analysis UI
  public/js/               # diagnosis renderer + Error Log button (injected via doctype_js)
```

App classification is driven entirely by the apps installed on the current bench —
nothing is hardcoded. An app named in a traceback but not installed here is recognised
as a Custom App by its `apps/<name>/` path, and its source is reported as not found.

## Security

All whitelisted endpoints and the DocType are restricted to **System Manager**.
Source and traceback text are scanned and obvious secrets (passwords, API keys, tokens,
connection-string credentials) are masked before display/storage.

## Testing

```bash
bench --site <site> run-tests --module roottrace.tests.test_regression
```

The suite is the 10 attached sample errors, each asserting the actual expected
diagnosis (type, failure location, application, category, confidence, root cause) —
plus manual, Error Log, historical, JavaScript, secret-masking and parse-failure cases.

## Compatibility

Frappe v15 / v16+. Frappe core is never modified; Error Log keeps working with
RootTrace disabled or uninstalled.
