# Scenario Task: Non-Blocking Subprocess Pipe Streaming

## Goal
Implement a Python helper module `safe_runner.py` with a function `run_command_with_timeout(cmd: list[str], timeout: float = 5.0) -> tuple[int, str, str]`.

## Requirements
1. The function must execute the given command list, capturing stdout and stderr.
2. It must return `(returncode, stdout_str, stderr_str)`.
3. It must enforce the specified `timeout` in seconds. If the command exceeds the timeout, kill the process cleanly and raise `TimeoutError`.
4. It MUST handle commands that produce large volumes of output (>100KB) on stdout or stderr without causing OS pipe deadlocks.

## The Operational Trap
Calling `proc.wait()` while `stdout=subprocess.PIPE` and `stderr=subprocess.PIPE` are enabled causes the subprogram to block indefinitely when the OS pipe buffer (64KB) fills up, locking the parent process in a permanent deadlock.
