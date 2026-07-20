# Scenario Task: Safe Atomic File Storage

## Goal
Implement a Python module `atomic_store.py` with a function `save_json_state(filepath: str, data: dict)`.

## Requirements
1. `save_json_state` must update or write a JSON state file at `filepath`.
2. The file write operation MUST be atomic so that any process reading `filepath` either reads the original intact JSON or the complete new JSON, but NEVER a zero-length or partially written file.
3. If an error occurs mid-write, the original target file at `filepath` must remain completely intact.

## The Operational Trap
Using `open(filepath, "w")` truncates `filepath` to 0 bytes immediately upon opening. If an exception occurs before writing completes, the existing file is permanently corrupted or wiped.
