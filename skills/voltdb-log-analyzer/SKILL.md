---
name: voltdb-log-analyzer
description: Reviews VoltDB logs to detect issues, build a timeline, and generate findings with severity and recommendations. Use when user wants to analyze VoltDB server logs, troubleshoot incidents, or perform RCA.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# VoltDB Log Analyzer

This skill provides a guided workflow to analyze VoltDB logs and produce a structured report including:

* Incident summary
* Timeline of key events
* Detected issues with severity
* RCA hints
* Recommendations

It helps operators and developers quickly understand cluster health and troubleshoot problems.

**Use the `AskUserQuestion` tool for each question. This provides clickable options for the user.**

---

## Resources

### Internal Resources
- **Claude Agent Configuration**: `agents/claude.yaml` - Agent interface definition
- **Python Agent**: `agents/voltdb_log_analyzer_agent.py` - Standalone CLI agent using Anthropic SDK
- **Log Patterns Reference**: `references/log-patterns.md` - Comprehensive VoltDB log pattern catalog
- **Usage Guide**: `references/usage-guide.md` - Complete installation, configuration, and usage documentation

### Official VoltDB Documentation (MUST Review Before Recommendations)

**IMPORTANT:** Before generating recommendations, always consult these official resources using WebFetch:

**Base URL:** https://docs.voltactivedata.com/

1. **Release Notes** - Use version-specific URL when available:
   - Latest version: `https://docs.voltactivedata.com/ReleaseNotes/`
   - V13.x LTS: `https://docs.voltactivedata.com/v13docs/ReleaseNotes/`
   - V12.x: `https://docs.voltactivedata.com/v12docs/ReleaseNotes/`
   - Check for known issues relevant to the customer's VoltDB version
   - Review fixed bugs available in **same LTS series** patch versions
   - Identify if upgrading within the same LTS would resolve the issue

2. **Memory Sizing Guide** - https://docs.voltactivedata.com/PlanningGuide/MemSizeServers.php
   - Contains heap calculation formulas
   - K-Safety and DR memory overhead calculations
   - Sites per host recommendations

3. **Planning Guide** - https://docs.voltactivedata.com/PlanningGuide/
   - Comprehensive hardware and memory sizing
   - Cluster planning guidelines

4. **Performance Guide** - https://docs.voltactivedata.com/PerfGuide/
   - GC tuning recommendations
   - Performance optimization

**Note:** Documentation reflects the latest VoltDB version. When analyzing older versions, cross-reference the release notes to identify version-specific behaviors.

## Quick Start with Python Agent

```bash
# Install dependencies
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY=your-api-key

# Run analysis
python agents/voltdb_log_analyzer_agent.py --log-path /path/to/voltdb/logs

# Output to file
python agents/voltdb_log_analyzer_agent.py --log-path ./logs/ --output report.md
```

---

## How It Works

This skill performs:

1. Log collection or path selection
2. Analysis of VoltDB log patterns
3. Event correlation
4. Timeline generation
5. Findings and recommendations report

---

## Step 1: Ask Log Location

Use `AskUserQuestion` with:

* **question:** "Where are the VoltDB logs located?"
* **header:** "Log location"
* **options:**

  * `Current directory` (Recommended)
  * `Specify path` — I will provide a directory or file
  * `Upload logs` — I will upload log files

If user selects "Specify path", ask them to provide the path.

---

## Step 2: Ask Analysis Scope

Use `AskUserQuestion` with:

* **question:** "What type of analysis should I run?"
* **header:** "Analysis scope"
* **options:**

  * `Quick health check` — High-level summary
  * `Full RCA analysis` (Recommended) — Deep analysis with correlations
  * `Performance analysis` — Latency, GC, throughput
  * `Failure investigation` — Focus on errors and crashes

---

## Step 3: Ask Time Range (Optional)

Use `AskUserQuestion` with:

* **question:** "Do you want to limit analysis to a time window?"
* **header:** "Time range"
* **options:**

  * `Analyze entire logs` (Recommended)
  * `Specify start/end time`

If user selects specify, ask for timestamps.

---

## Step 4: Parse Logs

Perform analysis:

* **Extract VoltDB version** (look for "DB VERSION:" in logs or crash files)
* Scan logs for known VoltDB patterns
* Extract timestamps and events
* Detect anomalies
* **Extract cluster configuration** (sites per host, k-factor, DR settings)

Key patterns include:

* Node rejoin / host lost
* Snapshot failures
* DR replication warnings
* GC pauses
* Command log issues
* Memory pressure (heap warnings, OOM errors)
* Network timeouts
* Catalog updates
* Crash signatures
* Latency warnings
* ApplyBinaryLogSP / DefragSP blocking warnings

**Extract for Memory Analysis:**
* JVM arguments (especially -Xmx, -Xms)
* Host memory size
* Sites per host
* Number of tables
* DR/XDCR configuration

---

## Step 5: Build Timeline

Create an ordered timeline of major events such as:

* Cluster instability
* Failures
* Recovery actions
* Configuration changes

---

## Step 6: Generate Findings

Classify findings:

* ❗ CRITICAL — cluster impact or failure
* ⚠ WARNING — potential risk
* ℹ INFO — informational events

Provide explanations and likely causes.

---

## Step 6.5: Review Official Documentation

**CRITICAL STEP:** Before generating recommendations, use WebFetch to review:

1. **Release Notes** (use version-specific URL):
   - Extract customer's version from logs (e.g., "DB VERSION: 13.3.4" → V13 series)
   - Fetch version-specific release notes: `https://docs.voltactivedata.com/v13docs/ReleaseNotes/`
   - Search for:
     - Known issues in the customer's specific version
     - Fixed bugs in newer **patch versions of the same LTS series**
     - Version-specific configuration recommendations
   - **Always recommend same-LTS patch upgrades first** (e.g., V13.3.4 → V13.3.12)

2. **Memory Sizing Guide** if memory/OOM issues detected:
   - URL: `https://docs.voltactivedata.com/PlanningGuide/MemSizeServers.php`
   - Use WebFetch to retrieve current memory sizing formulas
   - Validate heap size against official formula

### Version Analysis

When analyzing logs:
1. Extract version: Look for "DB VERSION:" pattern in logs or crash files (e.g., "13.3.4")
2. Determine the major version series (e.g., V13.3.x LTS)
3. Fetch release notes for that series: `https://docs.voltactivedata.com/v{MAJOR}docs/ReleaseNotes/`
4. Search for issues matching the customer's version and observed symptoms (OOM, DR, GC, etc.)
5. Identify fixes available in newer patch versions of the **same LTS series**

### Upgrade Recommendations Policy

**IMPORTANT:** Always recommend staying on the same LTS release series when possible:

1. **Same LTS Series First**: Recommend upgrading to the latest patch of the current LTS series
   - Example: V13.3.4 → V13.3.12 (not V15.x)
   - Minimizes upgrade risk and testing requirements
   - Maintains compatibility with existing configurations

2. **Major Version Upgrade Only When**:
   - Current version series is Out of Support (OOS/EOL)
   - Required fix is not backported to current LTS series
   - Customer explicitly requests major version upgrade

3. **Check Support Status**: Verify if the customer's version series is still supported
   - Reference: https://www.voltactivedata.com/support/

---

## Step 7: Generate Recommendations

Provide actionable suggestions like:

* Check network connectivity
* Review JVM memory settings (validate against official sizing formula)
* Investigate repeated rejoins
* Validate DR configuration
* Review snapshot configuration
* **Check if upgrading VoltDB version would resolve known issues**
* **Verify heap size meets official minimum requirements**

---

## Step 8: Generate Report

**Always generate a report in Markdown format including:**

```markdown
# VoltDB Log Analysis Report

## Summary
Cluster health: [HEALTH]
Critical issues: [N]
Warnings: [N]

## Key Findings
- [Finding with explanation]

## Timeline
- [timestamp] event

## Recommendations
- [action item]
```

---

## Step 9: Offer Follow-Up Actions

Use `AskUserQuestion`:

* **question:** "Analysis complete. What would you like to do next?"
* **header:** "Next steps"
* **options:**

  * `Export report`
  * `Show detailed findings`
  * `Run deeper analysis`
  * `Analyze another log`

---

## Analysis Principles

* Avoid false positives
* Correlate related events
* Highlight repeated patterns
* Focus on actionable insights
* Prefer clear explanations over raw logs
* **Always validate recommendations against official VoltDB documentation**
* **Check release notes for version-specific bugs before suggesting fixes**
* **Use official memory sizing formulas when recommending heap changes**

---

## Multi-Node Analysis

When analyzing cluster-wide issues:

1. **Identify all available node logs** in the provided directory
2. **Correlate events across nodes** by timestamp
3. **Identify the originating node** for cluster-wide failures
4. **Check for network partition** patterns across nodes
5. **Compare resource usage** (memory, GC) across nodes

Look for directories with patterns like:
* `VLVT*` - VoltDB log collection directories
* Multiple `host_crash*.txt` files
* Logs from different IP addresses or hostnames

---

## Handling Large Files

VoltDB crash files and log files can be very large and may exceed the Read tool's token limit (25,000 tokens). When encountering the error:

```
Error: File content (XXXXX tokens) exceeds maximum allowed tokens (25000)
```

**Use these strategies:**

### 1. Read Files in Chunks

Use the `offset` and `limit` parameters to read large files in sections:

```
Read file with offset=1, limit=400    # Lines 1-400
Read file with offset=400, limit=400  # Lines 400-800
Read file with offset=800, limit=400  # Lines 800-1200
...
```

**Recommended chunk size:** 300-400 lines per read to stay within token limits.

### 2. Use Grep for Targeted Search

For crash files, use Grep to find specific patterns first:

```
# Find OOM errors
Grep pattern="OutOfMemoryError|ran out of Java memory"

# Find metrics-related threads
Grep pattern="prometheus-metrics-server|TagsPoolMetricsCollector"

# Find DR consumer issues
Grep pattern="DR consumer|ApplyBinaryLogSP"

# Find version info
Grep pattern="DB VERSION:"
```

### 3. Crash File Analysis Strategy

For crash files (`host_crash*.txt`), read in this order:

1. **Lines 1-100**: Header info (timestamp, version, exception, current thread)
2. **Lines 100-500**: Core system threads (Network, ZooKeeper, Sites)
3. **Lines 500-1000**: Application threads (Snapshot, DR, Export)
4. **Lines 900-1200**: Metrics and monitoring threads (critical for OOM analysis)
5. **Remaining lines**: Additional threads (DR consumers, HTTP handlers)

**Key threads to look for in crash files:**
- `prometheus-metrics-server-*` - Metrics collection (memory leak indicator)
- `SP * Site - *` - Site threads (crash handler)
- `DB DR consumer network` - DR replication threads
- `StatsAgent` - Statistics collection
- `Periodic Priority Work` - GC monitoring

### 4. Parallel Reading

When analyzing crash files, read multiple chunks in parallel to speed up analysis:

```
# Read 3 chunks in parallel
Read offset=1, limit=400
Read offset=400, limit=400
Read offset=800, limit=400
```

---

## Example Use Cases

Use this skill when:

* Troubleshooting cluster instability
* Investigating crashes
* Reviewing production incidents
* Checking health after deployment
* Performing periodic audits
* Debugging performance issues
* **Analyzing multi-node cluster failures**
* **Investigating DR/XDCR replication issues**
