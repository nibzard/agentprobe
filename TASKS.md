# AgentProbe Development Tasks

## Task Management Style Guide

### Priority Levels
- 🔴 **P0 (Critical)**: Must be done immediately, blocks other work
- 🟠 **P1 (High)**: Important features, should be next in queue  
- 🟡 **P2 (Medium)**: Nice to have, implement when P0/P1 done
- 🟢 **P3 (Low)**: Future enhancements, not urgent

### Task Format
```
- [ ] [P#] Task description (Assignee: @name) [Status: Not Started/In Progress/Done]
  - [ ] Subtask 1
  - [ ] Subtask 2
```

### Status Tracking
- **Not Started**: Task hasn't begun
- **In Progress**: Currently being worked on
- **Blocked**: Waiting on dependencies
- **Review**: Implementation complete, needs review
- **Done**: Fully complete and tested

### Completion Tracking
- Mark tasks with `[x]` when complete
- Add completion date: `[Done: 2025-01-20]`
- Strike through entire line when archived: `~~- [x] [P1] Completed task~~`

---

## Phase 1: Results Storage System

### 🟠 P1: Implement Result Persistence
- [ ] [P1] Add SQLite database for storing test results [Status: Not Started]
  - [ ] Create database schema (results, traces, metadata)
  - [ ] Add storage.py module with ResultStore class
  - [ ] Update runner.py to save results after each test
  - [ ] Add result retrieval methods
  - [ ] Add database migrations support

### 🟠 P1: Result History Management  
- [ ] [P1] Track results over time for trend analysis [Status: Not Started]
  - [ ] Add timestamp and version tracking
  - [ ] Implement result comparison methods
  - [ ] Create result aggregation queries
  - [ ] Add cleanup for old results (configurable retention)
  - [ ] Add result tagging/labeling system

### 🟡 P2: Export Functionality
- [ ] [P2] Add CSV/JSON export for results [Status: Not Started]
  - [ ] Export single test results
  - [ ] Export benchmark results
  - [ ] Export aggregated statistics
  - [ ] Add filter options for exports
  - [ ] Support bulk export operations

---

## Phase 2: Enhanced Analysis Engine

### 🟠 P1: Command Pattern Analysis
- [ ] [P1] Parse actual CLI commands from traces [Status: Not Started]
  - [ ] Extract command patterns from message content
  - [ ] Build command frequency analysis
  - [ ] Identify successful vs failed command patterns
  - [ ] Track command sequence analysis
  - [ ] Detect command correction attempts

### 🟠 P1: Error Pattern Detection
- [x] [P1] Implement smart error categorization [Status: Done] [Done: 2025-01-20]
  - [x] Parse error messages from traces (via Claude analysis in analyzer.py:410-466)
  - [x] Categorize errors by type (auth, missing deps, syntax, etc) (Claude-based categorization)
  - [x] Map errors to recommendations (Claude provides specific recommendations)
  - [ ] Add per-tool error patterns
  - [ ] Create error frequency reports
  
**Implementation**: Enhanced with subprocess-based Claude Code SDK analysis for intelligent error categorization and recommendations, plus basic pattern detection fallback.

### 🟡 P2: Learning Curve Metrics
- [ ] [P2] Measure AI learning efficiency [Status: Not Started]
  - [ ] Track turns to first success
  - [ ] Measure help usage patterns
  - [ ] Identify exploration vs execution phases
  - [ ] Calculate efficiency scores
  - [ ] Compare learning curves across tools

### 🟡 P2: Tool Usage Analytics
- [ ] [P2] Deep analysis of tool interactions [Status: Not Started]
  - [ ] Track which CLI subcommands are used
  - [ ] Measure flag/option usage patterns
  - [ ] Identify common parameter combinations
  - [ ] Detect workflow patterns

---

## Phase 3: Advanced Reporting

### 🟠 P1: Complete Report Command
- [ ] [P1] Implement report generation functionality [Status: Not Started]
  - [ ] Load results from storage
  - [ ] Generate markdown reports
  - [ ] Generate HTML reports with charts
  - [ ] Generate JSON reports for programmatic use
  - [ ] Add report templates system
  
**Note**: Basic terminal reporting is implemented in reporter.py with rich formatting, success/failure detection, and aggregated statistics. However, the full report command in cli.py:172 is stub only - no file-based report generation.

### 🟠 P1: CLI Usability Scoring
- [ ] [P1] Create scoring algorithm for CLI friendliness [Status: Not Started]
  - [ ] Define scoring criteria (help quality, error clarity, etc)
  - [ ] Implement scoring calculations
  - [ ] Add comparative scoring across tools
  - [ ] Generate improvement recommendations
  - [ ] Create scoring rubric documentation

### 🟡 P2: Trend Analysis Reports
- [ ] [P2] Show performance over time [Status: Not Started]
  - [ ] Success rate trends
  - [ ] Cost trends
  - [ ] Duration trends
  - [ ] Compare versions/releases
  - [ ] Add anomaly detection

### 🟡 P2: Interactive Dashboard
- [ ] [P2] Create web-based results viewer [Status: Not Started]
  - [ ] Simple Flask/FastAPI server
  - [ ] Real-time result updates
  - [ ] Interactive charts and filters
  - [ ] Export capabilities from UI

---

## Additional Features

### 🟢 P3: Scenario Management
- [ ] [P3] Enhanced scenario system [Status: Not Started]
  - [ ] Scenario metadata (difficulty, category, etc)
  - [ ] Scenario dependencies
  - [ ] Conditional scenarios
  - [ ] Scenario validation

### 🟢 P3: Plugin System
- [ ] [P3] Extensibility for custom analyzers [Status: Not Started]
  - [ ] Plugin architecture design
  - [ ] Custom analyzer API
  - [ ] Plugin discovery mechanism
  - [ ] Documentation for plugin development

---

## Current Implementation Status (Updated 2025-01-20)

### ✅ What's Currently Working
- Core CLI framework (test, benchmark commands) - cli.py
- Claude Code SDK integration - runner.py
- Enhanced trace analysis with subprocess-based Claude analysis - analyzer.py
- Rich terminal reporting with success/failure detection - reporter.py
- Multi-run aggregation and statistics
- Comprehensive scenario library (vercel, gh, docker, git, wrangler)

### ❌ Major Missing Features
- **No persistence layer**: Results are not stored, only displayed
- **No historical tracking**: Cannot compare runs over time
- **No export capabilities**: Cannot save results to files
- **Report command is stub only**: cli.py:172 just shows placeholder message
- **No command pattern analysis**: Only basic error detection implemented
- **No CLI usability scoring**: No algorithmic assessment of tool friendliness

---

## Implementation Timeline

### Week 1 (Current)
- [x] Set up development environment [Done: 2025-01-20]
- [ ] Create storage.py foundation
- [ ] Implement basic SQLite storage
- [ ] Update runner to save results

### Week 2
- [ ] Complete result persistence
- [ ] Start command pattern analysis
- [ ] Implement error categorization

### Week 3
- [ ] Complete analysis engine
- [ ] Implement report generation
- [ ] Add CLI usability scoring

### Week 4+
- [ ] Polish and optimize
- [ ] Add trend analysis
- [ ] Documentation updates
- [ ] Performance improvements

---

## Technical Decisions

### Database Choice: SQLite
- Embedded, no server needed
- Perfect for local development
- Easy to backup/share
- Can migrate to PostgreSQL later if needed

### Report Formats Priority
1. Markdown (easiest, git-friendly)
2. JSON (programmatic use)
3. HTML (visual reports)
4. CSV (data analysis)

### Analysis Focus
- Start with simple pattern matching
- Add ML-based analysis later
- Keep analysis pluggable

---

## Notes
- Each feature should include unit tests
- Update README.md as features are added
- Maintain backwards compatibility
- Consider performance for large result sets
- Keep storage format versioned for migrations