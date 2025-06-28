# Memory Management Status

## 🧠 Current Session Context

### ✅ Established Key Information
- **Project**: SuiteSparse Matrix Collection Downloader (ssdownload)
- **Main Issue**: Incorrect matrix data, PART file pollution, wrong --spd logic
- **Priority**: CRITICAL fixes first (CSV source, PART files, SPD filtering)
- **Documentation**: Comprehensive restructured (README.md + docs/)

### 📋 Critical Tasks (From TODO.md)
1. Switch CSV: `sparse-files.engr.tamu.edu` → `sparse.tamu.edu/files/ssstats.csv`
2. Fix PART file pollution with existence checks
3. Implement correct --spd logic (symmetric AND posdef)

### 🗂️ Key Files Identified
- `src/ssdownload/config.py` - URL configurations
- `src/ssdownload/index_manager.py` - CSV data processing  
- `src/ssdownload/downloader.py` - File download logic
- `src/ssdownload/filters.py` - --spd filtering logic
- `src/ssdownload/cli_utils.py` - CLI option parsing

### 📊 Known Data Issues
- Wrong CSV source URL in config.py:36
- 16 duplicate entries in cache (2136 total, 2120 unique)
- nos5 example: should show Matrix ID 221, Date 1982, Author H. Simon

## 🔄 Memory Management Protocol

### When to Clear Memory
Run this command to clear context and start fresh:
```
CLEAR_MEMORY_CHECKPOINT
```

### What Gets Preserved
- TODO.md (complete task list)
- MEMORY_STATUS.md (this file)
- CLAUDE.md (development protocols)
- All source code changes made

### What Gets Cleared
- Detailed file analysis in memory
- Long conversation context
- Temporary investigation results

## 🚨 Quick Reference for Restart

If memory is cleared, read these files to restore context:
1. **TODO.md** - Complete task breakdown and priorities
2. **MEMORY_STATUS.md** - This summary
3. **CLAUDE.md** - Development and documentation protocols

### Critical File Locations
```
Config URL fix needed: src/ssdownload/config.py line 36
CSV_INDEX_URL = "https://sparse.tamu.edu/files/ssstats.csv"

PART file logic: src/ssdownload/downloader.py
SPD filter logic: src/ssdownload/filters.py + cli_utils.py
```

### Test Commands After Changes
```bash
# Test correct CSV source
uv run ssdl info nos5

# Test SPD filtering  
uv run ssdl list --spd --limit 5

# Test PART file cleanup
uv run ssdl download ct20stif  # Should not create .part debris
```

## 📈 Progress Tracking

### ✅ Completed
- [x] Problem analysis and root cause identification
- [x] Comprehensive TODO.md creation
- [x] Documentation restructuring (README.md + docs/)
- [x] Memory management setup

### 🚧 Next Steps (CRITICAL)
- [ ] Fix CSV source URL in config.py
- [ ] Implement PART file existence checks
- [ ] Fix --spd logic to combine symmetric + posdef

### 🔍 Testing Strategy
After each fix:
1. Test with known matrix (nos5) 
2. Verify no .part files left behind
3. Confirm --spd returns only SPD matrices
4. Update CHANGELOG.md with changes

## 💡 Memory Efficiency Tips

### For Long Sessions
1. Work on one CRITICAL task at a time
2. Test and commit after each fix
3. Use MEMORY_STATUS.md to track progress
4. Clear memory between major phases if needed

### Signs Memory Needs Clearing
- Responses become slower or less accurate
- Context from early conversation interferes
- Difficulty focusing on current task

### Restart Protocol
1. Say "CLEAR_MEMORY_CHECKPOINT" 
2. I'll read TODO.md and MEMORY_STATUS.md
3. Continue from where we left off
4. Update progress in MEMORY_STATUS.md