# Pipeline Health Dashboard

## Requirements
See [requirements.md](requirements.md) for project objectives and detailed feature descriptions.

## Running the Live Simulation
```bash
python run_live_simulation.py
```

This will start a 25-tick live simulation with real-time dashboard updates. The simulation shows:
- Pipeline health metrics and queue status
- SLO tracking with pass/fail indicators  
- Incident detection for violations
- Human inspection sampling

Press `Ctrl+C` to stop the simulation early.

## Sample output
See [sample_output.txt](sample_output.txt) for example simulation output.