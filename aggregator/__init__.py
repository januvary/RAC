"""
Aggregator — reads unit databases directly and produces per-unit stats.

No event logs, no replicas, no snapshots. Each unit's registros.db is the
source of truth; the aggregator opens them read-only and polls for changes
via file modification time.
"""
