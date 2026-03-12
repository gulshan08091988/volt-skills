#!/usr/bin/env python3
"""
VoltDB Log Analyzer - Claude Custom Agent

This agent analyzes VoltDB server logs to detect issues, build timelines,
and generate findings with severity and recommendations.

Usage:
    python voltdb_log_analyzer_agent.py --log-path /path/to/voltdb/logs

Requirements:
    pip install anthropic
"""

import argparse
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

try:
    import anthropic
except ImportError:
    print("Please install the anthropic package: pip install anthropic")
    exit(1)


# VoltDB Log Patterns
VOLTDB_PATTERNS = {
    "critical": [
        (r"FATAL|CRASH|OutOfMemoryError|StackOverflowError", "Fatal error or crash"),
        (r"Lost connection to host|Host .* failed", "Host failure"),
        (r"Snapshot failed|snapshot failure", "Snapshot failure"),
        (r"Command log corruption|CommandLogReinitiator", "Command log corruption"),
        (r"Data corruption|Checksum mismatch", "Data corruption"),
        (r"Unrecoverable error", "Unrecoverable error"),
        (r"Cluster partition detected", "Network partition"),
    ],
    "warning": [
        (r"GC pause exceeded|GC overhead|GCInspector", "GC pause warning"),
        (r"Memory pressure|heap usage", "Memory pressure"),
        (r"Rejoin started|Rejoining cluster", "Node rejoin"),
        (r"DR connection lost|Replication lag", "DR replication issue"),
        (r"Timeout|timed out|Connection timeout", "Timeout warning"),
        (r"Backpressure|backpressured", "Backpressure warning"),
        (r"Latency exceeded|slow query", "Latency warning"),
        (r"Retry attempt|Retrying", "Retry warning"),
    ],
    "info": [
        (r"Catalog update|Schema change", "Catalog update"),
        (r"Node joined|joined the cluster", "Node joined"),
        (r"Snapshot completed|Snapshot saved", "Snapshot completed"),
        (r"Server initialized|VoltDB starting", "Server startup"),
        (r"Graceful shutdown|shutdown requested", "Graceful shutdown"),
    ],
}


@dataclass
class LogEntry:
    """Represents a parsed log entry."""
    timestamp: Optional[datetime]
    level: str
    message: str
    raw_line: str
    line_number: int


@dataclass
class Finding:
    """Represents an analysis finding."""
    severity: str  # CRITICAL, WARNING, INFO
    category: str
    description: str
    log_entries: list = field(default_factory=list)
    recommendation: str = ""


@dataclass
class AnalysisReport:
    """Represents the complete analysis report."""
    log_path: str
    analysis_time: datetime
    total_lines: int
    findings: list = field(default_factory=list)
    timeline: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


class VoltDBLogAnalyzer:
    """VoltDB Log Analyzer using Claude."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer with Anthropic API key."""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    def parse_log_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line into structured format."""
        # Common VoltDB log format: YYYY-MM-DD HH:MM:SS,mmm LEVEL [thread] message
        pattern = r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},?\d*)\s+(\w+)\s+\[([^\]]+)\]\s+(.*)"
        match = re.match(pattern, line)

        if match:
            timestamp_str, level, thread, message = match.groups()
            try:
                # Handle timestamps with or without milliseconds
                timestamp_str = timestamp_str.replace(",", ".")
                if "." in timestamp_str:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                timestamp = None

            return LogEntry(
                timestamp=timestamp,
                level=level.upper(),
                message=message,
                raw_line=line,
                line_number=line_number
            )

        return None

    def detect_patterns(self, log_entries: list[LogEntry]) -> list[Finding]:
        """Detect known VoltDB patterns in log entries."""
        findings = []

        for severity, patterns in VOLTDB_PATTERNS.items():
            for pattern, category in patterns:
                matching_entries = []
                for entry in log_entries:
                    if re.search(pattern, entry.message, re.IGNORECASE):
                        matching_entries.append(entry)

                if matching_entries:
                    finding = Finding(
                        severity=severity.upper(),
                        category=category,
                        description=f"Detected {len(matching_entries)} occurrences of {category}",
                        log_entries=matching_entries[:10],  # Limit to 10 examples
                        recommendation=self._get_recommendation(category)
                    )
                    findings.append(finding)

        return findings

    def _get_recommendation(self, category: str) -> str:
        """Get recommendation for a finding category."""
        recommendations = {
            "Fatal error or crash": "Review crash dump and heap analysis. Check for resource exhaustion.",
            "Host failure": "Check network connectivity and hardware health. Review cluster topology.",
            "Snapshot failure": "Verify disk space and permissions. Check snapshot configuration.",
            "Command log corruption": "Review command log settings. May require cluster restart.",
            "Data corruption": "Contact VoltDB support immediately. Do not restart without backup.",
            "Network partition": "Review network infrastructure. Consider split-brain prevention settings.",
            "GC pause warning": "Tune JVM heap settings. Consider increasing heap or adjusting GC algorithm.",
            "Memory pressure": "Monitor heap usage. Consider increasing memory or optimizing queries.",
            "Node rejoin": "Investigate cause of node departure. Check for recurring patterns.",
            "DR replication issue": "Check DR configuration and network between clusters.",
            "Timeout warning": "Review network latency and query performance.",
            "Backpressure warning": "Reduce incoming load or scale cluster capacity.",
            "Latency warning": "Optimize slow queries. Review indexing strategy.",
            "Retry warning": "Investigate underlying cause of retries.",
            "Catalog update": "Informational - verify schema changes were intentional.",
            "Node joined": "Informational - verify cluster membership is expected.",
            "Snapshot completed": "Informational - verify snapshot schedule is correct.",
            "Server startup": "Informational - verify startup parameters.",
            "Graceful shutdown": "Informational - verify shutdown was intentional.",
        }
        return recommendations.get(category, "Review log entries for additional context.")

    def build_timeline(self, findings: list[Finding]) -> list[dict]:
        """Build a timeline of events from findings."""
        timeline = []

        for finding in findings:
            for entry in finding.log_entries:
                if entry.timestamp:
                    timeline.append({
                        "timestamp": entry.timestamp.isoformat(),
                        "severity": finding.severity,
                        "category": finding.category,
                        "message": entry.message[:200],  # Truncate long messages
                        "line": entry.line_number
                    })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        return timeline

    def analyze_with_claude(self, log_content: str, findings: list[Finding]) -> str:
        """Use Claude to provide deeper analysis."""
        findings_summary = "\n".join([
            f"- [{f.severity}] {f.category}: {f.description}"
            for f in findings
        ])

        # Truncate log content if too long
        max_log_length = 50000
        if len(log_content) > max_log_length:
            log_content = log_content[:max_log_length] + "\n... (truncated)"

        prompt = f"""Analyze the following VoltDB log content and findings. Provide:
1. An executive summary of cluster health
2. Root cause analysis for any critical issues
3. Correlations between events
4. Priority-ordered recommendations

## Detected Findings:
{findings_summary}

## Log Content Sample:
```
{log_content}
```

Provide your analysis in a structured format."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            system="You are a VoltDB expert analyzing database server logs. Focus on actionable insights and root cause analysis. Be concise but thorough."
        )

        return message.content[0].text

    def analyze_logs(self, log_path: str, time_range: Optional[tuple] = None) -> AnalysisReport:
        """Perform complete log analysis."""
        log_path = Path(log_path)

        if not log_path.exists():
            raise FileNotFoundError(f"Log path not found: {log_path}")

        # Collect log files
        if log_path.is_dir():
            log_files = list(log_path.glob("*.log")) + list(log_path.glob("voltdb*.log*"))
        else:
            log_files = [log_path]

        if not log_files:
            raise ValueError(f"No log files found in: {log_path}")

        # Parse all log entries
        all_entries = []
        all_content = []
        total_lines = 0

        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    all_content.extend(lines)
                    for i, line in enumerate(lines, 1):
                        total_lines += 1
                        entry = self.parse_log_line(line.strip(), total_lines)
                        if entry:
                            # Filter by time range if specified
                            if time_range and entry.timestamp:
                                start, end = time_range
                                if not (start <= entry.timestamp <= end):
                                    continue
                            all_entries.append(entry)
            except Exception as e:
                print(f"Warning: Could not read {log_file}: {e}")

        # Detect patterns
        findings = self.detect_patterns(all_entries)

        # Build timeline
        timeline = self.build_timeline(findings)

        # Get Claude analysis
        log_sample = "".join(all_content[:1000])  # First 1000 lines as sample
        claude_analysis = self.analyze_with_claude(log_sample, findings)

        # Generate summary
        summary = {
            "total_entries": len(all_entries),
            "critical_count": len([f for f in findings if f.severity == "CRITICAL"]),
            "warning_count": len([f for f in findings if f.severity == "WARNING"]),
            "info_count": len([f for f in findings if f.severity == "INFO"]),
            "cluster_health": "CRITICAL" if any(f.severity == "CRITICAL" for f in findings) else
                             "DEGRADED" if any(f.severity == "WARNING" for f in findings) else "HEALTHY",
            "claude_analysis": claude_analysis
        }

        return AnalysisReport(
            log_path=str(log_path),
            analysis_time=datetime.now(),
            total_lines=total_lines,
            findings=findings,
            timeline=timeline,
            summary=summary
        )

    def generate_markdown_report(self, report: AnalysisReport) -> str:
        """Generate a Markdown format report."""
        md = []
        md.append("# VoltDB Log Analysis Report\n")
        md.append(f"**Generated:** {report.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append(f"**Log Path:** `{report.log_path}`\n")
        md.append(f"**Total Lines Analyzed:** {report.total_lines:,}\n")

        # Summary
        md.append("\n## Summary\n")
        md.append(f"- **Cluster Health:** {report.summary['cluster_health']}\n")
        md.append(f"- **Critical Issues:** {report.summary['critical_count']}\n")
        md.append(f"- **Warnings:** {report.summary['warning_count']}\n")
        md.append(f"- **Informational Events:** {report.summary['info_count']}\n")

        # Claude Analysis
        if report.summary.get("claude_analysis"):
            md.append("\n## AI Analysis\n")
            md.append(report.summary["claude_analysis"])
            md.append("\n")

        # Key Findings
        md.append("\n## Key Findings\n")

        # Group by severity
        for severity in ["CRITICAL", "WARNING", "INFO"]:
            severity_findings = [f for f in report.findings if f.severity == severity]
            if severity_findings:
                emoji = {"CRITICAL": "!!!", "WARNING": "!!", "INFO": "i"}[severity]
                md.append(f"\n### {emoji} {severity}\n")
                for finding in severity_findings:
                    md.append(f"\n#### {finding.category}\n")
                    md.append(f"{finding.description}\n")
                    if finding.log_entries:
                        md.append("\n**Example log entries:**\n```\n")
                        for entry in finding.log_entries[:3]:
                            md.append(f"Line {entry.line_number}: {entry.raw_line[:200]}\n")
                        md.append("```\n")
                    md.append(f"\n**Recommendation:** {finding.recommendation}\n")

        # Timeline
        if report.timeline:
            md.append("\n## Timeline\n")
            md.append("| Timestamp | Severity | Event | Message |\n")
            md.append("|-----------|----------|-------|--------|\n")
            for event in report.timeline[:50]:  # Limit to 50 events
                msg = event["message"][:80] + "..." if len(event["message"]) > 80 else event["message"]
                md.append(f"| {event['timestamp']} | {event['severity']} | {event['category']} | {msg} |\n")

        # Recommendations Summary
        md.append("\n## Recommendations Summary\n")
        seen_recommendations = set()
        for finding in report.findings:
            if finding.recommendation and finding.recommendation not in seen_recommendations:
                md.append(f"- {finding.recommendation}\n")
                seen_recommendations.add(finding.recommendation)

        md.append("\n---\n")
        md.append("*Report generated by VoltDB Log Analyzer Agent*\n")

        return "".join(md)


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="VoltDB Log Analyzer - Claude Custom Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python voltdb_log_analyzer_agent.py --log-path /var/log/voltdb/
    python voltdb_log_analyzer_agent.py --log-path ./voltdb.log --output report.md
    python voltdb_log_analyzer_agent.py --log-path ./logs/ --format json
        """
    )
    parser.add_argument("--log-path", required=True, help="Path to VoltDB log file or directory")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")

    args = parser.parse_args()

    try:
        analyzer = VoltDBLogAnalyzer(api_key=args.api_key)
        print(f"Analyzing logs at: {args.log_path}")

        report = analyzer.analyze_logs(args.log_path)

        if args.format == "markdown":
            output = analyzer.generate_markdown_report(report)
        else:
            output = json.dumps({
                "log_path": report.log_path,
                "analysis_time": report.analysis_time.isoformat(),
                "total_lines": report.total_lines,
                "summary": report.summary,
                "findings": [
                    {
                        "severity": f.severity,
                        "category": f.category,
                        "description": f.description,
                        "recommendation": f.recommendation
                    }
                    for f in report.findings
                ],
                "timeline": report.timeline[:100]  # Limit timeline in JSON output
            }, indent=2)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Report saved to: {args.output}")
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
