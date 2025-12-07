# VS Code Explorer Tips (Windows/Linux) - Improve Folder Hierarchy View

If Explorer shows a flat list or many strangely named files (e.g., `C/`), use these steps to show hierarchical, readable tree and hide noisy entries.

1. Open project folder (preferred)
- Use `File` → `Open Folder...` and select the repository root `keibabook`.
- If you open individual files directly (e.g., `Open File...`), Explorer won't show a full folder tree.

2. Workspace config and multi-root
- If you use `keibabook.code-workspace`, open it via `File -> Open Workspace` to retain multi-root settings.

3. Explorer settings for readability
- `Explorer: Compact Folders` (controls whether single-child folders are collapsed into single line). Turn OFF to see true folder nesting. To change, run command `Ctrl+Shift+P` → `Preferences: Open Settings (UI)` and search `compact folders`.

4. Hide noisy or OS-specific artifacts
- If you see `C/` or other copied windows path folders, hide them in workspace settings (keibabook.code-workspace) or user settings in a `folders` override:

Example (Workspace settings):
```
"files.exclude": {
  "C/**": true,
  "**/.venv": true,
  "**/.pytest_cache": true
}
```

5. Use _Filter_ in Explorer
- Press Ctrl+Shift+F to globally search or use the Explorer filter (`Files: Exclude` / `Search: Exclude`) to exclude patterns interactively.

6. Use Tree / List modes for clarity
- Use `View` → `Appearance` → `Show Active File in Side Bar` to highlight current file location in tree.

7. Quick Tree Generation (CLI)
- If you want a quick folder tree to paste into docs or PRs, run:

```bash
# from repo root
find . -maxdepth 3 -type d -print | sed 's|^./||'
```

8. Final
- Recommended: Open the repo root (not files), set `Explorer: Compact Folders` to `false`, and add a few `files.exclude` patterns for `.venv`, `__pycache__`, and `C/` path artifacts.

If you want, I can add a `.vscode/settings.json` with friendly defaults to hide these noisy artifacts and improve Explorer readability.
