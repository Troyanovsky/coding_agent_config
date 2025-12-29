# Issues

## sync_commands.py

### Medium Priority

- [x] Remove duplicate `target_roo_root` variable definition (lines ~73 and ~147)
- [x] Remove unused `expand_path()` function (defined but never called)
- [x] Refactor code duplication between Claude and Roo extraction sections (identical logic in lines ~107-140 and ~144-177)
- [x] Standardize error handling patterns (inconsistent between symlink creation, removal, and file operations)

### Low Priority

- [ ] Handle directory cleanup in symlink section (if user replaces symlink with directory of same name)
- [ ] Consider adding configuration file for target directories instead of hardcoding