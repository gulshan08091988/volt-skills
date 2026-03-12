---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
style: |
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
  }
  h1 {
    color: #1a5490;
  }
  h2 {
    color: #2d7dd2;
  }
  code {
    background-color: #f4f4f4;
  }
  table {
    font-size: 0.8em;
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
---

# VoltDB Log Analyzer

## AI-Powered Log Analysis & Root Cause Detection

**Powered by Claude AI**

![bg right:40% 80%](https://img.icons8.com/fluency/512/database.png)

---

# The Problem

## Challenges with VoltDB Log Analysis

- **Volume**: Thousands of log entries across multiple nodes
- **Complexity**: Correlating events across distributed cluster
- **Time-consuming**: Manual analysis takes hours
- **Expertise required**: Need deep VoltDB knowledge
- **Missed patterns**: Human review may overlook subtle issues

---

# The Solution

## VoltDB Log Analyzer Agent

An intelligent Claude-powered agent that automatically:

| Capability | Description |
|------------|-------------|
| **Detect** | Identify critical issues, warnings, and anomalies |
| **Correlate** | Connect related events across time and nodes |
| **Analyze** | Perform root cause analysis using AI |
| **Report** | Generate structured findings with recommendations |

---

# Key Features

## What It Does

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Log Input   │ --> │ AI Analysis  │ --> │Report Output │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ Single file  │     │Pattern detect│     │Health status │
│ Directory    │     │ Correlation  │     │ Timeline     │
│ Multi-node   │     │     RCA      │     │ Findings     │
└──────────────┘     └──────────────┘     └──────────────┘
```

- **20+ built-in** VoltDB-specific patterns
- **Timeline generation** of events
- **Severity classification** (Critical/Warning/Info)
- **Actionable recommendations**

---

# Pattern Detection

## What We Detect

### Critical (Cluster Impact)
- Host failures & network partitions
- Snapshot failures
- Command log corruption
- Out of memory errors

### Warning (Performance Risk)
- GC pauses & memory pressure
- Backpressure warnings
- DR replication lag
- Latency warnings

### Informational
- Catalog updates, Node joins, Snapshots

---

# Architecture

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                  VoltDB Log Analyzer                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────┐   │
│  │   Log    │   │ Pattern  │   │    Claude AI      │   │
│  │  Parser  │-->│ Detector │-->│  Deep Analysis    │   │
│  └──────────┘   └──────────┘   └───────────────────┘   │
│       │              │                  │               │
│       v              v                  v               │
│  ┌─────────────────────────────────────────────────┐   │
│  │            Report Generator                      │   │
│  │   Markdown | JSON | Timeline | Recommendations   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

# Sample Report Output

## Analysis Report Structure

```markdown
# VoltDB Log Analysis Report

## Summary
- Cluster Health: CRITICAL
- Critical Issues: 3
- Warnings: 12

## AI Analysis
Executive summary with root cause...

## Key Findings
- [CRITICAL] Host 192.168.1.10 failed
- [WARNING] GC pauses exceeding threshold

## Recommendations
1. Check network connectivity
2. Review JVM heap settings
```

---

# Use Cases

## When to Use

| Scenario | Benefit |
|----------|---------|
| **Incident Response** | Rapid RCA during outages |
| **Production Troubleshooting** | Identify issues before escalation |
| **Post-Incident Review** | Comprehensive post-mortem analysis |
| **Health Audits** | Periodic cluster health checks |
| **Performance Analysis** | Identify latency and GC issues |
| **Deployment Validation** | Verify health after changes |

---

# Quick Start

## Getting Started in 3 Steps

### 1. Install
```bash
pip install anthropic
```

### 2. Configure
```bash
export ANTHROPIC_API_KEY="your-key"
```

### 3. Run
```bash
python voltdb_log_analyzer_agent.py \
  --log-path /var/log/voltdb/ \
  --output report.md
```

---

# Integration Options

## Deployment Modes

**CLI Tool**
```bash
python voltdb_log_analyzer_agent.py --log-path ./logs
```

**Python Module**
```python
from voltdb_log_analyzer_agent import VoltDBLogAnalyzer
analyzer = VoltDBLogAnalyzer()
report = analyzer.analyze_logs("/path/to/logs")
```

**Automation**: Cron jobs, CI/CD, Monitoring webhooks

**Alerts**: Slack, PagerDuty, Email notifications

---

# Benefits

## Why Use VoltDB Log Analyzer?

| Traditional | With Log Analyzer |
|-------------|-------------------|
| Hours of manual review | **Minutes** to insights |
| Requires VoltDB expertise | **AI-assisted** analysis |
| May miss correlations | **Automatic** event linking |
| Ad-hoc troubleshooting | **Structured**, repeatable |
| Text-based logs only | **Actionable** reports |

### ROI
- **Faster MTTR** - Reduce incident resolution time
- **Proactive Detection** - Find issues before impact

---

# Technical Specifications

## Components

| Component | Details |
|-----------|---------|
| **AI Model** | Claude Sonnet 4 |
| **Language** | Python 3.9+ |
| **Dependencies** | anthropic SDK |
| **Output Formats** | Markdown, JSON |

## Project Structure
```
voltdb-log-analyzer/
├── agents/
│   ├── claude.yaml
│   └── voltdb_log_analyzer_agent.py
├── references/
│   ├── log-patterns.md
│   └── usage-guide.md
└── SKILL.md
```

---

# Roadmap

## Future Enhancements

### Near-term
- Time-range filtering
- Custom pattern configuration
- Compressed log support

### Medium-term
- Real-time log streaming
- Multi-cluster comparison
- Anomaly prediction

### Long-term
- Interactive dashboard
- Historical trend analysis
- Automated remediation

---

# Demo

## Live Demonstration

1. **Input**: Sample VoltDB logs with known issues

2. **Process**: Run analyzer against logs

3. **Output**: Review generated report

4. **Discuss**: Walk through findings and recommendations

---

# Questions?

## Resources

- **Usage Guide**: `references/usage-guide.md`
- **Pattern Reference**: `references/log-patterns.md`
- **VoltDB Docs**: https://docs.voltdb.com

## Contact

- Repository issues for bug reports
- Feature requests welcome

---

# Appendix A: Supported Patterns

## Critical Patterns

| Pattern | Category |
|---------|----------|
| FATAL, CRASH, OutOfMemoryError | Fatal error |
| Host.*failed, Lost connection | Host failure |
| Snapshot failed | Snapshot failure |
| Command log corruption | Command log issue |
| Cluster partition detected | Network partition |

## Warning Patterns

| Pattern | Category |
|---------|----------|
| GC pause exceeded | GC warning |
| Memory pressure | Memory issue |
| Rejoin started | Node rejoin |
| DR connection lost | DR issue |
| Backpressure | Backpressure |

---

# Appendix B: Sample Commands

## Common Usage Patterns

```bash
# Basic analysis
python voltdb_log_analyzer_agent.py --log-path ./logs

# Save to file
python voltdb_log_analyzer_agent.py --log-path ./logs -o report.md

# JSON output
python voltdb_log_analyzer_agent.py --log-path ./logs --format json

# Multiple clusters
for cluster in cluster1 cluster2; do
  python voltdb_log_analyzer_agent.py \
    --log-path /logs/$cluster \
    --output ${cluster}_report.md
done
```
