# Quick Start - Trigger Monitor

## 1. Post a Trigger Message

```bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [architect] [TRIGGER] @sylvia @roy: Review and implement feature X" >> chatroom/triggers.txt
```

## 2. Run Monitor (One-Shot Test)

```bash
cd /Users/annhoward/src/superalignment-chatroom
python3 scripts/trigger-monitor.py --once
```

## 3. Check Agent Logs

```bash
ls -lt logs/trigger_*.log | head -2
tail -50 logs/trigger_sylvia_*.log
```

## 4. Run Continuously

```bash
# Foreground (Ctrl+C to stop)
python3 scripts/trigger-monitor.py --interval 30

# Background (daemon)
nohup python3 scripts/trigger-monitor.py --interval 30 > logs/trigger-monitor.log 2>&1 &
```

## Trigger Format

```
[TIMESTAMP] [SENDER] [TRIGGER] @agent1 @agent2: Your message here
```

## Agent Delays

- sylvia: 0s (first)
- cynthia: 5s
- roy: 10s
- moss: 15s
- tessa: 20s
- historian: 25s
- architect: 30s
- ray: 35s
- orchestrator: 40s (last)

**Full docs:** `TRIGGER_MONITOR.md`
