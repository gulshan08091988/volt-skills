# VoltDB Log Patterns Reference

This document catalogs common VoltDB log patterns for analysis and troubleshooting.

## Log Format

VoltDB logs typically follow this format:
```
YYYY-MM-DD HH:MM:SS,mmm LEVEL [thread-name] message
```

Example:
```
2024-01-15 10:23:45,123 INFO [main] VoltDB Server version 12.0 starting
```

## Severity Levels

| Level | Description |
|-------|-------------|
| FATAL | Unrecoverable errors causing shutdown |
| ERROR | Errors requiring attention |
| WARN  | Potential issues |
| INFO  | Informational messages |
| DEBUG | Debug-level details |
| TRACE | Fine-grained tracing |

---

## Critical Patterns

### Cluster Failures

#### Host Lost
```
Pattern: Host .* failed|Lost connection to host
Example: Host 192.168.1.10 failed. Cluster now has 2 hosts
```
**Cause:** Network partition, hardware failure, or node crash
**Action:** Check network connectivity, review hardware health

#### Network Partition
```
Pattern: Cluster partition detected|split brain
Example: Cluster partition detected: 2 nodes in partition A, 1 node in partition B
```
**Cause:** Network infrastructure failure
**Action:** Review network topology, consider split-brain prevention

### Data Integrity

#### Snapshot Failure
```
Pattern: Snapshot failed|snapshot failure|SnapshotSaveAPI
Example: Snapshot failed: disk space exhausted
```
**Cause:** Disk full, permission issues, I/O errors
**Action:** Check disk space, verify snapshot directory permissions

#### Command Log Corruption
```
Pattern: Command log corruption|CommandLogReinitiator error
Example: Command log segment corrupted at offset 12345
```
**Cause:** Disk failure, improper shutdown
**Action:** Review disk health, may require recovery from snapshot

#### Data Corruption
```
Pattern: Data corruption|Checksum mismatch
Example: Checksum mismatch in tuple at partition 5
```
**Cause:** Memory corruption, disk failure, software bug
**Action:** Contact VoltDB support immediately

### Memory Issues

#### Out of Memory
```
Pattern: OutOfMemoryError|OOM|Java heap space|ran out of Java memory
Example: java.lang.OutOfMemoryError: Java heap space
Example: FATAL [SP 9 Site - 0:6] HOST: Site: 0:6 ran out of Java memory. This node will shut down.
```
**Cause:** Insufficient heap, memory leak, large result sets, DR buffer overflow
**Action:**
- Calculate required heap using official formula: `384MB + (10MB × tables) + (sites_per_host × 256MB for DR)`
- Review JVM arguments for -Xmx/-Xms settings
- Check for known memory leaks in VoltDB release notes

#### Heap Pressure Warning
```
Pattern: Heap is \d+% full|GC: Heap is
Example: WARN [Periodic Priority Work] GC: Heap is 98.43% full out of 20000.00MB.
```
**Cause:** Approaching memory exhaustion, memory leak, undersized heap
**Action:**
- Monitor trend (progressive increase indicates leak or sizing issue)
- Heap >90% sustained requires immediate attention
- Compare against official memory sizing requirements

#### Time-Keeper Thread Stalls
```
Pattern: time-keeper thread has not been updated for
Example: HOST: The internal time-keeper thread has not been updated for 57.719 seconds
```
**Cause:** Severe GC pressure causing JVM thread starvation
**Action:** Critical indicator of impending OOM, increase heap immediately

#### Long-Running Procedures Blocking Queues
```
Pattern: blocking the queue for site|procedure.*taking a long time
Example: HOST: The procedure DefragSP is taking a long time -- over 10 seconds -- and blocking the queue for site 10
Example: HOST: The procedure ApplyBinaryLogSP is taking a long time -- over 10 seconds
```
**Cause:** Memory pressure causing slow operations, GC pauses
**Action:** Indicates system under stress, check heap utilization

---

## Warning Patterns

### Performance

#### GC Pauses
```
Pattern: GC pause exceeded|GC overhead|GCInspector
Example: GC pause of 1523ms exceeds threshold of 500ms
```
**Cause:** Heap pressure, insufficient memory, large objects
**Action:** Tune JVM settings, increase heap, review memory usage

#### Backpressure
```
Pattern: Backpressure|backpressured|queue full
Example: Transaction queue backpressured, rejecting new requests
```
**Cause:** Cluster overwhelmed, slow queries, insufficient resources
**Action:** Reduce load, scale out, optimize queries

#### Latency Warnings
```
Pattern: Latency exceeded|slow query|execution time
Example: Query execution time 5234ms exceeds threshold 1000ms
```
**Cause:** Complex queries, missing indexes, resource contention
**Action:** Optimize queries, add indexes, review execution plans

### Cluster Health

#### Node Rejoin
```
Pattern: Rejoin started|Rejoining cluster|rejoin in progress
Example: Node 192.168.1.10 rejoining cluster
```
**Cause:** Previous node failure, network reconnection
**Action:** Monitor rejoin progress, investigate original cause

#### DR Replication Issues
```
Pattern: DR connection lost|Replication lag|DR queue|DRAGENT|DR consumer
Example: DR replication lag: 5000ms
Example: ERROR [DB DR consumer network Network - 0] org.voltcore.network.VoltNetwork: Exception in network thread
Example: DRAGENT: DR CRC check configuration
```
**Cause:** Network issues, target cluster load, configuration mismatch, memory pressure
**Action:** Check network, review DR configuration, verify consumer buffer limits

#### XDCR Specific Issues
```
Pattern: XDCR|ApplyBinaryLogSP|DR consumer|DR producer
Example: WARN [SP 3 Site - 5:2] DRAGENT: Database is not empty table ACB_CERTIFICATE_CACHE has 337 rows.
Example: HOST: The procedure ApplyBinaryLogSP is taking a long time
```
**Cause:** Replication catching up, memory pressure on consumer, network latency
**Action:**
- Check DR consumer limit configuration (`<maxsize>` in deployment.xml)
- Review consumer cluster heap sizing (requires 256MB × sites_per_host overhead)
- Check VoltDB release notes for known XDCR issues in your version

#### DR Connection Configuration
```
Pattern: Configured connection for DR|connectionTimeout|receivetimeout
Example: HOST: Configured connection for DR replica role to host 10.116.210.31:21218 with connectionTimeout: 10000
```
**Info:** DR connection settings for troubleshooting timeout issues

### Timeouts

#### Connection Timeouts
```
Pattern: Timeout|timed out|Connection timeout
Example: Connection to host 192.168.1.10 timed out after 30000ms
```
**Cause:** Network issues, overloaded nodes
**Action:** Review network latency, check target node health

---

## Informational Patterns

### Startup/Shutdown

#### Server Startup
```
Pattern: VoltDB starting|Server initialized|Initialization complete
Example: VoltDB Server version 12.0 (Build: abc123) starting
```

#### Graceful Shutdown
```
Pattern: Graceful shutdown|shutdown requested|Shutting down
Example: Graceful shutdown requested, waiting for transactions to complete
```

### Configuration

#### Catalog Updates
```
Pattern: Catalog update|Schema change|DDL statement
Example: Catalog update completed: added table USERS
```

#### Node Membership
```
Pattern: Node joined|joined the cluster|Host added
Example: Host 192.168.1.12 joined the cluster
```

### Operations

#### Snapshot Completed
```
Pattern: Snapshot completed|Snapshot saved|SnapshotSaveAPI success
Example: Snapshot completed successfully: /data/snapshots/snap_20240115_1023
```

---

## Analysis Workflow

1. **Initial Scan**: Search for FATAL and ERROR level entries
2. **Time Correlation**: Build timeline of events
3. **Pattern Matching**: Identify known issues using patterns above
4. **Root Cause**: Trace back from symptoms to causes
5. **Recommendations**: Provide actionable remediation steps

## Common Analysis Queries

### Find all errors in time range
```bash
grep -E "ERROR|FATAL" voltdb.log | awk '$1 >= "2024-01-15" && $1 <= "2024-01-16"'
```

### Count occurrences by category
```bash
grep -oE "(GC pause|Timeout|Rejoin|Snapshot)" voltdb.log | sort | uniq -c | sort -rn
```

### Extract timeline of critical events
```bash
grep -E "FATAL|Host.*failed|partition detected|corruption" voltdb.log | head -50
```

---

## Version Information Patterns

#### Extract VoltDB Version
```
Pattern: DB VERSION:|VoltDB Server version
Example: DB VERSION: 13.3.4
Example: VoltDB Server version 13.3.4 (Build: abc123)
```
**Use:** Identify version for release notes lookup

#### JVM Configuration
```
Pattern: Command line JVM arguments:|Xmx|Xms
Example: HOST: Command line JVM arguments: -Xmx20000m -Xms20000m -XX:+UseG1GC
```
**Use:** Extract heap configuration for sizing validation

#### Cluster Configuration
```
Pattern: sitesperhost|kfactor|hostcount|partitions
Example: Cluster sitesperhost="8" kfactor="1"
Example: org.voltdb.cluster.hostcount=5
```
**Use:** Extract cluster topology for memory calculation

---

## See Also

- [VoltDB Documentation](https://docs.voltactivedata.com/)
- [VoltDB Release Notes](https://docs.voltactivedata.com/ReleaseNotes/)
- [VoltDB Memory Sizing Guide](https://docs.voltactivedata.com/PlanningGuide/MemSizeServers.php)
- [VoltDB Planning Guide](https://docs.voltactivedata.com/PlanningGuide/)
- [VoltDB Performance Guide](https://docs.voltactivedata.com/PerfGuide/)
