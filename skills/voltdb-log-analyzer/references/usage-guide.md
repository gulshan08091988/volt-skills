# VoltDB Log Analyzer - Usage Guide

This guide covers installation, configuration, and usage of the VoltDB Log Analyzer Claude custom agent.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Basic Usage](#basic-usage)
5. [Advanced Usage](#advanced-usage)
6. [Understanding Reports](#understanding-reports)
7. [Integration Examples](#integration-examples)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Prerequisites

- Python 3.9 or higher
- Anthropic API key (get one at https://console.anthropic.com)
- Access to VoltDB log files

### Supported Log Formats

The analyzer supports standard VoltDB log formats:
```
YYYY-MM-DD HH:MM:SS,mmm LEVEL [thread-name] message
```

Supported file types:
- `*.log` - Standard log files
- `voltdb*.log*` - VoltDB specific log files (including rotated logs)

---

## Installation

### Option 1: Direct Installation

```bash
# Navigate to the skill directory
cd voltdb-log-analyzer

# Install dependencies
pip install -r requirements.txt

# Or install directly
pip install anthropic
```

### Option 2: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Using pipx (Isolated Installation)

```bash
pipx install anthropic
```

### Verify Installation

```bash
python -c "import anthropic; print('Anthropic SDK installed successfully')"
```

---

## Configuration

### API Key Setup

**Option 1: Environment Variable (Recommended)**
```bash
# Linux/macOS - Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Windows Command Prompt
set ANTHROPIC_API_KEY=sk-ant-api03-...

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**Option 2: Command Line Argument**
```bash
python agents/voltdb_log_analyzer_agent.py --api-key "sk-ant-api03-..." --log-path ./logs
```

**Option 3: Configuration File**
Create `~/.voltdb-analyzer.conf`:
```ini
[anthropic]
api_key = sk-ant-api03-...
```

### Agent Configuration

The agent behavior is configured in `agents/claude.yaml`:

```yaml
agent:
  model: "claude-sonnet-4-20250514"  # Model to use
  max_tokens: 8192                    # Max response tokens
  temperature: 0.1                    # Lower = more deterministic
```

---

## Basic Usage

### Analyze a Single Log File

```bash
python agents/voltdb_log_analyzer_agent.py --log-path /var/log/voltdb/voltdb.log
```

### Analyze a Directory of Logs

```bash
python agents/voltdb_log_analyzer_agent.py --log-path /var/log/voltdb/
```

### Save Report to File

```bash
# Markdown format (default)
python agents/voltdb_log_analyzer_agent.py --log-path ./logs --output report.md

# JSON format
python agents/voltdb_log_analyzer_agent.py --log-path ./logs --output report.json --format json
```

### Quick Examples

```bash
# Analyze current directory logs
python agents/voltdb_log_analyzer_agent.py --log-path .

# Analyze with verbose output
python agents/voltdb_log_analyzer_agent.py --log-path ./logs 2>&1 | tee analysis.log

# Pipe to less for pagination
python agents/voltdb_log_analyzer_agent.py --log-path ./logs | less
```

---

## Advanced Usage

### Time-Range Filtering

Filter analysis to specific time windows (coming in future version):
```bash
python agents/voltdb_log_analyzer_agent.py \
  --log-path ./logs \
  --start-time "2024-01-15 10:00:00" \
  --end-time "2024-01-15 12:00:00"
```

### Batch Processing Multiple Clusters

```bash
#!/bin/bash
# analyze_all_clusters.sh

CLUSTERS=("cluster1" "cluster2" "cluster3")
OUTPUT_DIR="./reports/$(date +%Y%m%d)"

mkdir -p "$OUTPUT_DIR"

for cluster in "${CLUSTERS[@]}"; do
  echo "Analyzing $cluster..."
  python agents/voltdb_log_analyzer_agent.py \
    --log-path "/logs/$cluster/" \
    --output "$OUTPUT_DIR/${cluster}_report.md"
done

echo "Reports saved to $OUTPUT_DIR"
```

### Automated Daily Analysis

Create a cron job for automated analysis:
```bash
# Edit crontab
crontab -e

# Add daily analysis at 6 AM
0 6 * * * /path/to/venv/bin/python /path/to/voltdb_log_analyzer_agent.py \
  --log-path /var/log/voltdb/ \
  --output /reports/daily_$(date +\%Y\%m\%d).md \
  2>> /var/log/voltdb-analyzer.log
```

### Integration with Monitoring Systems

**Send to Slack:**
```bash
#!/bin/bash
REPORT=$(python agents/voltdb_log_analyzer_agent.py --log-path ./logs --format json)
CRITICAL_COUNT=$(echo "$REPORT" | jq '.summary.critical_count')

if [ "$CRITICAL_COUNT" -gt 0 ]; then
  curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"VoltDB Alert: $CRITICAL_COUNT critical issues found\"}" \
    "$SLACK_WEBHOOK_URL"
fi
```

**Send to PagerDuty:**
```bash
#!/bin/bash
REPORT=$(python agents/voltdb_log_analyzer_agent.py --log-path ./logs --format json)
HEALTH=$(echo "$REPORT" | jq -r '.summary.cluster_health')

if [ "$HEALTH" = "CRITICAL" ]; then
  curl -X POST https://events.pagerduty.com/v2/enqueue \
    -H 'Content-Type: application/json' \
    -d "{
      \"routing_key\": \"$PD_ROUTING_KEY\",
      \"event_action\": \"trigger\",
      \"payload\": {
        \"summary\": \"VoltDB Cluster Critical\",
        \"severity\": \"critical\",
        \"source\": \"voltdb-log-analyzer\"
      }
    }"
fi
```

---

## Understanding Reports

### Report Structure

The Markdown report includes these sections:

#### 1. Summary
```markdown
## Summary
- **Cluster Health:** CRITICAL | DEGRADED | HEALTHY
- **Critical Issues:** 3
- **Warnings:** 12
- **Informational Events:** 45
```

Health status meanings:
- **CRITICAL**: Cluster-impacting issues detected (failures, data loss risk)
- **DEGRADED**: Warnings present that may affect performance
- **HEALTHY**: No significant issues detected

#### 2. AI Analysis
Claude's deep analysis including:
- Executive summary
- Root cause identification
- Event correlations
- Priority recommendations

#### 3. Key Findings
Organized by severity:

```markdown
### !!! CRITICAL
#### Host failure
Detected 2 occurrences of Host failure
**Example log entries:**
Line 1234: 2024-01-15 10:23:45,123 ERROR Host 192.168.1.10 failed
**Recommendation:** Check network connectivity and hardware health.
```

#### 4. Timeline
Chronological event table:
```markdown
| Timestamp | Severity | Event | Message |
|-----------|----------|-------|---------|
| 2024-01-15T10:23:45 | CRITICAL | Host failure | Host 192.168.1.10 failed |
```

#### 5. Recommendations Summary
Deduplicated list of all recommendations.

### JSON Report Structure

```json
{
  "log_path": "/path/to/logs",
  "analysis_time": "2024-01-15T14:30:00",
  "total_lines": 50000,
  "summary": {
    "total_entries": 45000,
    "critical_count": 3,
    "warning_count": 12,
    "info_count": 45,
    "cluster_health": "CRITICAL",
    "claude_analysis": "..."
  },
  "findings": [...],
  "timeline": [...]
}
```

---

## Integration Examples

### As a Python Module

```python
from agents.voltdb_log_analyzer_agent import VoltDBLogAnalyzer

# Initialize analyzer
analyzer = VoltDBLogAnalyzer()

# Analyze logs
report = analyzer.analyze_logs("/var/log/voltdb/")

# Access results
print(f"Health: {report.summary['cluster_health']}")
print(f"Critical issues: {report.summary['critical_count']}")

# Generate Markdown report
markdown = analyzer.generate_markdown_report(report)
print(markdown)
```

### Custom Pattern Detection

```python
from agents.voltdb_log_analyzer_agent import VoltDBLogAnalyzer, VOLTDB_PATTERNS

# Add custom patterns
VOLTDB_PATTERNS["warning"].append(
    (r"Custom pattern here", "Custom category name")
)

# Run analysis with custom patterns
analyzer = VoltDBLogAnalyzer()
report = analyzer.analyze_logs("./logs")
```

### Webhook Receiver (Flask Example)

```python
from flask import Flask, request, jsonify
from agents.voltdb_log_analyzer_agent import VoltDBLogAnalyzer
import tempfile
import os

app = Flask(__name__)
analyzer = VoltDBLogAnalyzer()

@app.route('/analyze', methods=['POST'])
def analyze():
    # Receive log content
    log_content = request.data.decode('utf-8')

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        temp_path = f.name

    try:
        # Analyze
        report = analyzer.analyze_logs(temp_path)
        return jsonify({
            "health": report.summary['cluster_health'],
            "critical": report.summary['critical_count'],
            "warnings": report.summary['warning_count']
        })
    finally:
        os.unlink(temp_path)

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Troubleshooting

### Common Issues

#### "ANTHROPIC_API_KEY environment variable or api_key parameter required"
```bash
# Solution: Set the API key
export ANTHROPIC_API_KEY="your-api-key"
```

#### "No log files found"
```bash
# Check file permissions
ls -la /path/to/logs/

# Ensure log files exist and have .log extension
find /path/to/logs -name "*.log" -type f
```

#### "Rate limit exceeded"
The Anthropic API has rate limits. Solutions:
- Wait and retry
- Reduce log file size
- Use batch processing with delays

#### "Connection timeout"
```bash
# Check network connectivity
curl -I https://api.anthropic.com

# Set custom timeout (in code)
# Modify the anthropic client initialization
```

#### Memory issues with large logs
```bash
# For very large log files, split first
split -l 100000 large.log chunk_

# Analyze each chunk
for f in chunk_*; do
  python agents/voltdb_log_analyzer_agent.py --log-path "$f" --output "${f}_report.md"
done
```

### Debug Mode

Enable verbose logging:
```bash
# Set Python logging level
PYTHONVERBOSE=1 python agents/voltdb_log_analyzer_agent.py --log-path ./logs

# Or add to the script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verifying Log Format

Check if your logs match expected format:
```bash
# Show first few lines
head -5 /path/to/voltdb.log

# Expected format:
# 2024-01-15 10:23:45,123 INFO [main] Message here
```

---

## FAQ

### Q: How much does it cost to run an analysis?

The cost depends on log size. Approximately:
- Small logs (<1MB): ~$0.01-0.05
- Medium logs (1-10MB): ~$0.05-0.20
- Large logs (>10MB): ~$0.20-1.00

The agent samples logs to control costs for very large files.

### Q: Can I use a different Claude model?

Yes, modify `agents/claude.yaml` or the Python code:
```python
analyzer = VoltDBLogAnalyzer()
analyzer.model = "claude-opus-4-20250514"  # For more complex analysis
```

### Q: Does it work with compressed logs?

Not directly. Decompress first:
```bash
gunzip voltdb.log.gz
# or
zcat voltdb.log.gz > voltdb.log
```

### Q: Can I analyze logs from multiple clusters together?

Yes, copy logs to a single directory:
```bash
mkdir combined_logs
cp /cluster1/logs/*.log combined_logs/cluster1_
cp /cluster2/logs/*.log combined_logs/cluster2_
python agents/voltdb_log_analyzer_agent.py --log-path combined_logs/
```

### Q: How do I add custom patterns?

Edit `VOLTDB_PATTERNS` in `voltdb_log_analyzer_agent.py`:
```python
VOLTDB_PATTERNS = {
    "critical": [
        (r"Your pattern here", "Category name"),
        # ... existing patterns
    ],
    # ...
}
```

### Q: Is my data sent to Anthropic?

Yes, log content is sent to the Anthropic API for analysis. The agent samples logs (first ~1000 lines) to minimize data transfer. If you have sensitive data:
- Redact sensitive information before analysis
- Use the pattern-detection-only mode (modify code to skip Claude API call)
- Review Anthropic's data retention policies

---

## Support

For issues or feature requests:
- Check the [log patterns reference](./log-patterns.md)
- Review VoltDB documentation at https://docs.voltdb.com
- Open an issue in the repository

---

*Last updated: 2024*
