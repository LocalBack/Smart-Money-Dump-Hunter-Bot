# Chaos Testing Runbook

These scripts introduce failures to verify automatic recovery.

## kill-redis.sh / kill-redis.ps1
Stops the Redis container for 60 seconds and then restarts it.
The services should reconnect once Redis is back online. Check orchestrator logs for reconnection messages.

## cpu-spike.sh
Triggers a short CPU spike inside the `orchestrator` container for 20 seconds.
Expect increased latency but services should remain operational.

### Running
```bash
bash scripts/chaos/kill-redis.sh
bash scripts/chaos/cpu-spike.sh
```

### Expected Recovery
- Redis outage: collectors and orchestrator resume after container restarts.
- CPU spike: no permanent errors, Prometheus shows temporary latency spike.
