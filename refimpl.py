#!/usr/bin/env python3
"""Reference impl for: aw-alert-filters-s1-filter-dict-airlines-ua

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/alert_filters.py'
t = p.read_text()

OLD = '''"""Stub for src/alert_filters.py -- implement per TASK.md."""'''
NEW = '''def get_filter():
    return {'airlines': ['UA', 'NH'], 'max_points': 90000, 'max_taxes': 100.0}'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
