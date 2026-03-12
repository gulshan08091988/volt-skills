#!/usr/bin/env python3
"""
VoltDB Log Analyzer - Local Version (No API Required)

This agent analyzes VoltDB server logs using pattern matching only.
No external API calls - completely free to run.

Usage:
    python voltdb_log_analyzer_local.py --log-path /path/to/voltdb/logs

Optional (for AI-enhanced analysis):
    pip install ollama
    ollama pull llama3.1
    python voltdb_log_analyzer_local.py --log-path ./logs --use-ollama
"""

import argparse
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# Optional Ollama support
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


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

# Recommendations database
RECOMMENDATIONS = {
    "Fatal error or crash": [
        "Review crash dump and heap analysis",
        "Check for resource exhaustion (memory, disk, file descriptors)",
        "Examine recent code or configuration changes",
    ],
    "Host failure": [
        "Check network connectivity between cluster nodes",
        "Review hardware health (disk, memory, CPU)",
        "Examine system logs for OS-level issues",
    ],
    "Snapshot failure": [
        "Verify disk space on snapshot directory",
        "Check file permissions for snapshot path",
        "Review snapshot configuration settings",
    ],
    "Command log corruption": [
        "Check disk health and I/O errors",
        "Review command log directory permissions",
        "Consider recovery from latest snapshot",
    ],
    "Data corruption": [
        "STOP - Do not restart without contacting support",
        "Preserve all logs and data files",
        "Contact VoltDB support immediately",
    ],
    "Network partition": [
        "Review network infrastructure",
        "Check firewall rules between nodes",
        "Consider implementing split-brain prevention",
    ],
    "GC pause warning": [
        "Tune JVM heap size (-Xmx, -Xms)",
        "Consider G1GC or ZGC for large heaps",
        "Review memory usage patterns",
    ],
    "Memory pressure": [
        "Increase available heap memory",
        "Review query result set sizes",
        "Check for memory leaks in procedures",
    ],
    "Node rejoin": [
        "Monitor rejoin progress",
        "Investigate original cause of node departure",
        "Check for recurring patterns",
    ],
    "DR replication issue": [
        "Check network between DR clusters",
        "Review DR configuration",
        "Monitor replication queue depth",
    ],
    "Timeout warning": [
        "Review network latency",
        "Check target node health",
        "Consider increasing timeout values",
    ],
    "Backpressure warning": [
        "Reduce incoming transaction load",
        "Scale out cluster capacity",
        "Optimize slow procedures",
    ],
    "Latency warning": [
        "Review slow query execution plans",
        "Add or optimize indexes",
        "Check for lock contention",
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
    severity: str
    category: str
    description: str
    count: int = 0
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None
    log_entries: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


@dataclass
class AnalysisReport:
    """Represents the complete analysis report."""
    log_path: str
    analysis_time: datetime
    total_lines: int
    total_entries: int
    findings: list = field(default_factory=list)
    timeline: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    ai_analysis: str = ""


class VoltDBLogAnalyzerLocal:
    """VoltDB Log Analyzer - Local version without external API."""

    def __init__(self, use_ollama: bool = False, ollama_model: str = "llama3.1"):
        """Initialize the analyzer."""
        self.use_ollama = use_ollama and OLLAMA_AVAILABLE
        self.ollama_model = ollama_model

        if use_ollama and not OLLAMA_AVAILABLE:
            print("Warning: Ollama not installed. Running in pattern-only mode.")
            print("Install with: pip install ollama")

    def parse_log_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line into structured format."""
        # Common VoltDB log format
        pattern = r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},?\d*)\s+(\w+)\s+\[([^\]]+)\]\s+(.*)"
        match = re.match(pattern, line)

        if match:
            timestamp_str, level, thread, message = match.groups()
            try:
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
                    timestamps = [e.timestamp for e in matching_entries if e.timestamp]

                    finding = Finding(
                        severity=severity.upper(),
                        category=category,
                        description=f"Detected {len(matching_entries)} occurrence(s) of {category}",
                        count=len(matching_entries),
                        first_occurrence=min(timestamps) if timestamps else None,
                        last_occurrence=max(timestamps) if timestamps else None,
                        log_entries=matching_entries[:10],
                        recommendations=RECOMMENDATIONS.get(category, ["Review log entries for context"])
                    )
                    findings.append(finding)

        # Sort by severity
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        findings.sort(key=lambda f: (severity_order.get(f.severity, 3), -f.count))

        return findings

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
                        "message": entry.message[:200],
                        "line": entry.line_number
                    })

        timeline.sort(key=lambda x: x["timestamp"])
        return timeline

    def analyze_with_ollama(self, log_sample: str, findings: list[Finding]) -> str:
        """Use Ollama for local AI analysis."""
        if not self.use_ollama:
            return ""

        findings_summary = "\n".join([
            f"- [{f.severity}] {f.category}: {f.count} occurrences"
            for f in findings
        ])

        prompt = f"""You are a VoltDB database expert. Analyze the following log findings and provide:
1. Executive summary of cluster health (2-3 sentences)
2. Root cause analysis for critical issues
3. Priority-ordered action items

Findings:
{findings_summary}

Log sample:
{log_sample[:5000]}

Provide a concise, actionable analysis."""

        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            return f"(Ollama analysis unavailable: {e})"

    def generate_rule_based_summary(self, findings: list[Finding]) -> str:
        """Generate analysis summary using rules (no AI)."""
        critical = [f for f in findings if f.severity == "CRITICAL"]
        warnings = [f for f in findings if f.severity == "WARNING"]

        summary_parts = []

        # Health assessment
        if critical:
            summary_parts.append("CLUSTER HEALTH: CRITICAL - Immediate attention required.")
            summary_parts.append(f"\nCritical issues detected ({len(critical)}):")
            for f in critical:
                summary_parts.append(f"  - {f.category}: {f.count} occurrence(s)")
        elif warnings:
            summary_parts.append("CLUSTER HEALTH: DEGRADED - Performance issues detected.")
        else:
            summary_parts.append("CLUSTER HEALTH: HEALTHY - No significant issues detected.")

        # Key concerns
        if critical or warnings:
            summary_parts.append("\nKEY CONCERNS:")
            for f in (critical + warnings)[:5]:
                summary_parts.append(f"  - {f.category}")
                if f.first_occurrence and f.last_occurrence:
                    summary_parts.append(f"    First seen: {f.first_occurrence}")
                    summary_parts.append(f"    Last seen: {f.last_occurrence}")

        # Top recommendations
        all_recs = []
        for f in findings:
            all_recs.extend(f.recommendations)
        unique_recs = list(dict.fromkeys(all_recs))[:5]

        if unique_recs:
            summary_parts.append("\nTOP RECOMMENDATIONS:")
            for i, rec in enumerate(unique_recs, 1):
                summary_parts.append(f"  {i}. {rec}")

        return "\n".join(summary_parts)

    def analyze_logs(self, log_path: str) -> AnalysisReport:
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

        print(f"Found {len(log_files)} log file(s)")

        # Parse all log entries
        all_entries = []
        all_content = []
        total_lines = 0

        for log_file in log_files:
            print(f"  Processing: {log_file.name}")
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    all_content.extend(lines)
                    for i, line in enumerate(lines, 1):
                        total_lines += 1
                        entry = self.parse_log_line(line.strip(), total_lines)
                        if entry:
                            all_entries.append(entry)
            except Exception as e:
                print(f"  Warning: Could not read {log_file}: {e}")

        print(f"Parsed {len(all_entries)} log entries from {total_lines} lines")

        # Detect patterns
        print("Detecting patterns...")
        findings = self.detect_patterns(all_entries)
        print(f"Found {len(findings)} issue categories")

        # Build timeline
        timeline = self.build_timeline(findings)

        # Generate analysis
        rule_based_summary = self.generate_rule_based_summary(findings)

        ai_analysis = ""
        if self.use_ollama:
            print(f"Running AI analysis with {self.ollama_model}...")
            log_sample = "".join(all_content[:500])
            ai_analysis = self.analyze_with_ollama(log_sample, findings)

        # Generate summary
        summary = {
            "total_entries": len(all_entries),
            "critical_count": len([f for f in findings if f.severity == "CRITICAL"]),
            "warning_count": len([f for f in findings if f.severity == "WARNING"]),
            "info_count": len([f for f in findings if f.severity == "INFO"]),
            "cluster_health": "CRITICAL" if any(f.severity == "CRITICAL" for f in findings) else
                             "DEGRADED" if any(f.severity == "WARNING" for f in findings) else "HEALTHY",
        }

        return AnalysisReport(
            log_path=str(log_path),
            analysis_time=datetime.now(),
            total_lines=total_lines,
            total_entries=len(all_entries),
            findings=findings,
            timeline=timeline,
            summary=summary,
            ai_analysis=ai_analysis or rule_based_summary
        )

    def generate_markdown_report(self, report: AnalysisReport) -> str:
        """Generate a Markdown format report."""
        md = []
        md.append("# VoltDB Log Analysis Report\n")
        md.append(f"**Generated:** {report.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append(f"**Log Path:** `{report.log_path}`\n")
        md.append(f"**Total Lines Analyzed:** {report.total_lines:,}\n")
        md.append(f"**Parsed Entries:** {report.total_entries:,}\n")

        # Summary
        md.append("\n## Summary\n")
        health_emoji = {"CRITICAL": "!!!", "DEGRADED": "!!", "HEALTHY": "OK"}
        md.append(f"- **Cluster Health:** {health_emoji.get(report.summary['cluster_health'], '')} {report.summary['cluster_health']}\n")
        md.append(f"- **Critical Issues:** {report.summary['critical_count']}\n")
        md.append(f"- **Warnings:** {report.summary['warning_count']}\n")
        md.append(f"- **Informational Events:** {report.summary['info_count']}\n")

        # Analysis
        if report.ai_analysis:
            md.append("\n## Analysis\n")
            md.append("```\n")
            md.append(report.ai_analysis)
            md.append("\n```\n")

        # Key Findings
        md.append("\n## Key Findings\n")

        for severity in ["CRITICAL", "WARNING", "INFO"]:
            severity_findings = [f for f in report.findings if f.severity == severity]
            if severity_findings:
                emoji = {"CRITICAL": "!!!", "WARNING": "!!", "INFO": "i"}[severity]
                md.append(f"\n### {emoji} {severity}\n")

                for finding in severity_findings:
                    md.append(f"\n#### {finding.category}\n")
                    md.append(f"**Count:** {finding.count} occurrence(s)\n")

                    if finding.first_occurrence:
                        md.append(f"**Time Range:** {finding.first_occurrence} to {finding.last_occurrence}\n")

                    if finding.log_entries:
                        md.append("\n**Sample log entries:**\n```\n")
                        for entry in finding.log_entries[:3]:
                            md.append(f"Line {entry.line_number}: {entry.raw_line[:150]}\n")
                        md.append("```\n")

                    if finding.recommendations:
                        md.append("\n**Recommendations:**\n")
                        for rec in finding.recommendations:
                            md.append(f"- {rec}\n")

        # Timeline
        if report.timeline:
            md.append("\n## Event Timeline\n")
            md.append("| Timestamp | Severity | Event | Message |\n")
            md.append("|-----------|----------|-------|--------|\n")
            for event in report.timeline[:30]:
                msg = event["message"][:60] + "..." if len(event["message"]) > 60 else event["message"]
                msg = msg.replace("|", "\\|")
                md.append(f"| {event['timestamp']} | {event['severity']} | {event['category']} | {msg} |\n")

        md.append("\n---\n")
        md.append("*Report generated by VoltDB Log Analyzer (Local)*\n")

        return "".join(md)


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="VoltDB Log Analyzer - Local Version (No API Required)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic analysis (no AI, completely free)
    python voltdb_log_analyzer_local.py --log-path /var/log/voltdb/

    # With local AI (requires Ollama)
    python voltdb_log_analyzer_local.py --log-path ./logs --use-ollama

    # Save report
    python voltdb_log_analyzer_local.py --log-path ./logs -o report.md
        """
    )
    parser.add_argument("--log-path", required=True, help="Path to VoltDB log file or directory")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--use-ollama", action="store_true", help="Use Ollama for AI-enhanced analysis (free, local)")
    parser.add_argument("--ollama-model", default="llama3.1", help="Ollama model to use (default: llama3.1)")

    args = parser.parse_args()

    try:
        analyzer = VoltDBLogAnalyzerLocal(
            use_ollama=args.use_ollama,
            ollama_model=args.ollama_model
        )

        print(f"\n{'='*50}")
        print("VoltDB Log Analyzer (Local Version)")
        print(f"{'='*50}\n")

        report = analyzer.analyze_logs(args.log_path)

        if args.format == "markdown":
            output = analyzer.generate_markdown_report(report)
        else:
            output = json.dumps({
                "log_path": report.log_path,
                "analysis_time": report.analysis_time.isoformat(),
                "total_lines": report.total_lines,
                "summary": report.summary,
                "analysis": report.ai_analysis,
                "findings": [
                    {
                        "severity": f.severity,
                        "category": f.category,
                        "count": f.count,
                        "recommendations": f.recommendations
                    }
                    for f in report.findings
                ],
                "timeline": report.timeline[:100]
            }, indent=2)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"\nReport saved to: {args.output}")
        else:
            print("\n" + output)

    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
