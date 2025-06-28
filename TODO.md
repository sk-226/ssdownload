# Matrix Data Quality Fix - Task List

Fix for incorrect matrix information and data inconsistencies in `ssdl info` command and cached data.

## 🚨 Critical Issues Identified

- ✅ **Wrong CSV source**: ~~Using incorrect `sparse-files.engr.tamu.edu` instead of official `sparse.tamu.edu/files/ssstats.csv`~~ **FIXED**
- ✅ **Ineffective --spd option**: ~~Should auto-combine symmetric AND posdef conditions for SPD matrices~~ **FIXED**
- ✅ **PART file pollution**: ~~Duplicate downloads create .part file debris~~ **FIXED** (Already handled + clean command added)
- ✅ **Incorrect URLs**: ~~Using unofficial Heroku app instead of official site~~ **FIXED** (CSV source updated)
- ✅ **System cache management**: Added `ssdl clean-cache` command **NEW FEATURE**
- **16 duplicate entries** in cache (2136 total, 2120 unique names) - **PARTIALLY ADDRESSED**
- **Missing crucial metadata**: Matrix ID, authors, dates, SVD statistics
- **Data validation gaps**: No duplicate removal or integrity checks

## Phase 1: Data Source Investigation & Design (High Priority)

### Research & Discovery
- [x] **Switch to correct official CSV source** ✅ **COMPLETED**
  - [x] Change from `http://sparse-files.engr.tamu.edu/files/ssstats.csv`
  - [x] Use official `https://sparse.tamu.edu/files/ssstats.csv`
  - [x] Compare data format and quality differences
  - [x] Test data accuracy with known matrices (e.g., nos5)
- [ ] **Investigate official SuiteSparse API endpoints**
  - [ ] Check if `sparse.tamu.edu` has official API documentation
  - [ ] Test RSS feeds or structured data endpoints
  - [ ] Document rate limits and usage guidelines
- [ ] **Analyze current vs. correct data sources**
  - [ ] Compare CSV data format vs. official website data
  - [ ] Map missing fields (Matrix ID, authors, SVD stats, etc.)
  - [ ] Document data quality differences
- [ ] **Research web scraping alternatives**
  - [ ] Investigate robots.txt on sparse.tamu.edu
  - [ ] Test feasibility of scraping individual matrix pages
  - [ ] Evaluate ethical and technical considerations

### Data Model Design
- [ ] **Design new comprehensive matrix data structure**
  - [ ] Include Matrix ID, creation date, authors, editors
  - [ ] Add SVD statistics (condition number, singular values)
  - [ ] Include structural details (rank, symmetry percentages)
  - [ ] Define optional vs. required fields
- [ ] **Plan backward compatibility strategy**
  - [ ] Ensure existing API calls continue working
  - [ ] Design data migration strategy for existing cache
  - [ ] Plan versioning for cache format
- [ ] **Design duplicate detection logic**
  - [ ] Define unique key strategy (Matrix ID vs. group/name)
  - [ ] Plan duplicate resolution rules
  - [ ] Design data validation framework
- [x] **Redesign --spd option logic** ✅ **COMPLETED**
  - [x] Make --spd automatically imply symmetric=True AND posdef=True
  - [x] Remove redundant spd field from data structure if not needed
  - [x] Update filter logic to handle SPD as compound condition
  - [x] Ensure mathematical correctness (SPD ⊆ symmetric ∩ posdef)

## Phase 2: Data Acquisition Implementation (High Priority)

### PART File Management (Critical Fix) ✅ **COMPLETED**
- [x] **Implement pre-download file existence check** ✅ **COMPLETED**
  - [x] Check for existing complete files before starting download
  - [x] Clean up orphaned .part files from failed downloads
  - [x] Add file size and checksum validation for existing files
  - [x] Skip download if valid file already exists
- [x] **Improve download resume logic** ✅ **COMPLETED**
  - [x] Better .part file cleanup on successful completion
  - [x] Add .part file age checking (clean old abandoned downloads)
  - [x] Implement atomic file renaming (temp -> final)
  - [x] Add user command to clean .part files: `ssdl clean-cache`

### URL and Endpoint Updates ✅ **COMPLETED**
- [x] **Update configuration to use official sources** ✅ **COMPLETED**
  - [x] Change CSV_INDEX_URL to `https://sparse.tamu.edu/files/ssstats.csv`
  - [x] Change base URLs from Heroku to official sparse.tamu.edu
  - [x] Update file download endpoints
  - [x] Update checksum URL generation
- [ ] **Implement fallback mechanisms**
  - [ ] Primary: Official CSV from sparse.tamu.edu
  - [ ] Secondary: Official API (if available)
  - [ ] Tertiary: Web scraping with rate limiting
  - [ ] Fallback: Current CSV as minimal backup

### Enhanced Data Fetching
- [ ] **Implement individual matrix page scraping**
  - [ ] Create HTTP client with proper rate limiting
  - [ ] Parse individual matrix pages for detailed metadata
  - [ ] Extract SVD statistics and structural information
  - [ ] Handle parsing errors gracefully
- [ ] **Create progressive data enhancement**
  - [ ] Start with CSV for basic matrix list
  - [ ] Enhance with detailed page data on-demand
  - [ ] Cache enhanced data for future use
- [ ] **Add robust error handling**
  - [ ] Network timeout handling
  - [ ] Parse error recovery
  - [ ] Graceful degradation to basic data

## Phase 3: Data Processing & Validation (High Priority)

### Data Cleaning Implementation
- [ ] **Implement duplicate detection and removal**
  - [ ] Create unique key generation (group + name or Matrix ID)
  - [ ] Implement duplicate merging logic
  - [ ] Add data consistency validation
- [ ] **Add comprehensive data validation**
  - [ ] Validate matrix dimensions and constraints
  - [ ] Check data type consistency
  - [ ] Verify mathematical relationships (e.g., SPD implies symmetric)
- [ ] **Create data integrity framework**
  - [ ] Add checksum validation for cache files
  - [ ] Implement data freshness checks
  - [ ] Create corruption detection and recovery

### Enhanced Index Manager
- [ ] **Rewrite IndexManager with new data model**
  - [ ] Support progressive data loading
  - [ ] Implement efficient duplicate handling
  - [ ] Add data validation pipeline
- [ ] **Implement smart caching strategy**
  - [ ] Separate basic and detailed information caches
  - [ ] Add incremental update capability
  - [ ] Implement cache invalidation logic
- [ ] **Add data migration utilities**
  - [ ] Convert existing cache to new format
  - [ ] Provide rollback capability
  - [ ] Validate migration success

## Phase 4: Cache Strategy Improvement (Medium Priority)

### Multi-tier Cache Design
- [ ] **Implement layered cache architecture**
  - [ ] Level 1: Basic matrix list (fast loading)
  - [ ] Level 2: Enhanced metadata (on-demand)
  - [ ] Level 3: SVD statistics and detailed analysis
- [ ] **Add intelligent cache management**
  - [ ] Implement LRU eviction for detailed data
  - [ ] Add cache size monitoring and limits
  - [ ] Create background refresh for stale data
- [ ] **Optimize cache performance**
  - [ ] Use efficient serialization (consider binary formats)
  - [ ] Implement parallel cache loading
  - [ ] Add cache prewarming for popular matrices

### Cache Validation & Recovery
- [ ] **Add cache integrity checks**
  - [ ] Validate cache file format and structure
  - [ ] Check for data corruption
  - [ ] Verify timestamp consistency
- [ ] **Implement cache recovery mechanisms**
  - [ ] Automatic cache rebuild on corruption
  - [ ] Partial cache recovery strategies
  - [ ] User-triggered cache refresh commands

## Phase 5: User Interface Enhancement (Medium Priority)

### Enhanced `ssdl info` Command
- [ ] **Display comprehensive matrix information**
  - [ ] Show Matrix ID, creation date, authors
  - [ ] Display SVD statistics in user-friendly format
  - [ ] Include structural analysis results
- [ ] **Implement progressive information disclosure**
  - [ ] Basic info by default
  - [ ] `--detailed` flag for enhanced metadata
  - [ ] `--expert` flag for technical statistics
- [ ] **Add information formatting options**
  - [ ] JSON output for programmatic use
  - [ ] Table format for comparison
  - [ ] Rich console formatting with colors

### CLI Improvements
- [ ] **Add data validation commands**
  - [ ] `ssdl validate-cache` command
  - [ ] `ssdl refresh-cache` command
  - [ ] `ssdl repair-cache` command
  - [ ] `ssdl clean-cache` command (remove .part files)
- [ ] **Enhance search and filtering**
  - [ ] Search by Matrix ID
  - [ ] Filter by creation date range
  - [ ] Search by author or editor
- [ ] **Improve --spd option usability**
  - [ ] Make --spd automatically filter for symmetric AND positive definite
  - [ ] Add clear documentation that --spd implies both conditions
  - [ ] Consider adding --symmetric-only and --posdef-only for granular control
  - [ ] Update help text to explain SPD convenience
- [ ] **Add cache management commands**
  - [ ] Show cache statistics and health
  - [ ] Clear specific cache levels
  - [ ] Export/import cache data

## Phase 6: Testing & Documentation (Medium Priority)

### Comprehensive Testing
- [ ] **Create test suite for new data model**
  - [ ] Unit tests for data parsing and validation
  - [ ] Integration tests with official website
  - [ ] Performance tests for large datasets
- [ ] **Add edge case testing**
  - [ ] Network failure scenarios
  - [ ] Malformed data handling
  - [ ] Cache corruption recovery
- [ ] **Create end-to-end validation**
  - [ ] Compare data accuracy with official site
  - [ ] Validate all matrix information fields
  - [ ] Test duplicate detection effectiveness

### Documentation Updates
- [ ] **Update all documentation for new features**
  - [ ] CLI_REFERENCE.md with new commands and options
  - [ ] API_REFERENCE.md with enhanced data model
  - [ ] EXAMPLES.md with rich metadata usage
- [ ] **Add troubleshooting guides**
  - [ ] Cache corruption issues
  - [ ] Network connectivity problems
  - [ ] Data inconsistency resolution
- [ ] **Create data accuracy verification guide**
  - [ ] How to verify matrix information
  - [ ] When to refresh cache
  - [ ] How to report data issues

## Phase 7: Performance & Reliability (Low Priority)

### Performance Optimization
- [ ] **Optimize data fetching performance**
  - [ ] Implement concurrent matrix page fetching
  - [ ] Add connection pooling and keep-alive
  - [ ] Optimize parsing performance
- [ ] **Add monitoring and metrics**
  - [ ] Track cache hit rates
  - [ ] Monitor data fetching success rates
  - [ ] Log performance metrics
- [ ] **Implement background processing**
  - [ ] Background cache updates
  - [ ] Asynchronous data enhancement
  - [ ] Proactive stale data refresh

### Reliability Improvements
- [ ] **Add comprehensive logging**
  - [ ] Data source selection logic
  - [ ] Cache operations and failures
  - [ ] Data validation results
- [ ] **Implement health checks**
  - [ ] Data source availability monitoring
  - [ ] Cache integrity verification
  - [ ] System health reporting
- [ ] **Add graceful degradation**
  - [ ] Fallback to older cache on fetch failure
  - [ ] Partial functionality with incomplete data
  - [ ] User notification of degraded service

## Quality Assurance Checklist

### Before Implementation
- [ ] **Verify no malicious external dependencies**
- [ ] **Confirm ethical web scraping practices**
- [ ] **Document all external API usage**
- [ ] **Plan for rate limiting and respectful access**

### During Implementation
- [ ] **Follow existing code style and patterns**
- [ ] **Add comprehensive error handling**
- [ ] **Include proper type hints and documentation**
- [ ] **Write tests for all new functionality**

### After Implementation
- [ ] **Update CHANGELOG.md with all changes**
- [ ] **Test all documentation examples**
- [ ] **Verify backward compatibility**
- [ ] **Performance test with large datasets**

## Success Criteria

- [ ] **Data accuracy**: `ssdl info nos5` shows Matrix ID: 221, Date: 1982, Author: H. Simon
- [ ] **No duplicates**: Cache contains only unique matrices
- [ ] **Complete metadata**: All available official site data is captured
- [ ] **Performance**: Enhanced data loads within acceptable time limits
- [ ] **Reliability**: System gracefully handles network issues and data problems
- [ ] **Documentation**: All examples work and documentation is current
- [ ] **PART file cleanup**: No orphaned .part files after normal operations
- [ ] **SPD filtering works correctly**: `ssdl list --spd` returns only symmetric positive definite matrices
- [ ] **Official CSV integration**: Data comes from correct `sparse.tamu.edu/files/ssstats.csv` source

## Priority Order for Implementation

### 🚨 **CRITICAL (Fix Immediately)**
1. Switch CSV source to official `https://sparse.tamu.edu/files/ssstats.csv`
2. Fix PART file pollution with pre-download existence checks
3. Implement correct --spd logic (symmetric AND posdef)

### 🔥 **HIGH (Next Sprint)**
4. Remove duplicate entries from cache
5. Add `ssdl clean-cache` command for .part file cleanup
6. Update all URLs to official sparse.tamu.edu endpoints

### 📈 **MEDIUM (Following Sprints)**
7. Enhanced metadata collection from individual matrix pages
8. Improved cache management and validation
9. Extended CLI commands and options

### 🔧 **LOW (Future Enhancements)**
10. Performance optimizations
11. Advanced monitoring and metrics
12. Background processing features
