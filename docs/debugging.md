# Debugging Notes

This file records real debugging observations from implementation and verification.

## PowerShell Multi-Path `Get-ChildItem` Error

- Symptom: a Phase 5 repository inventory command failed with `A positional parameter cannot
  be found that accepts argument 'docs'`.
- Command: `Get-ChildItem -Recurse -File docs src tests scripts`
- Cause: this PowerShell invocation treated the extra path names as unexpected positional
  arguments for the selected parameter set.
- Resolution: used `rg --files docs src tests scripts`, which produced the intended file
  inventory without modifying the repository.

## Bare `uv` Not On PATH

- Symptom: this Windows shell did not expose a bare `uv` executable on `PATH` in earlier
  phases.
- Resolution: Phase 5 commands used the installed executable at
  `$env:APPDATA\Python\Python313\Scripts\uv.exe`.

