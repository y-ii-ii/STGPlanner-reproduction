#!/usr/bin/env bash
pkill -f '^python3 /mnt/d/STGPlanner/scripts/rviz_status_probe.py' || true
exec bash /mnt/d/STGPlanner/scripts/rviz_status_probe.sh /mnt/d/STGPlanner/logs/rviz_repair/status_after.json
