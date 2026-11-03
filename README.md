# Neuro Connect Four

Living neurons on a Cortical Labs CL1 play Connect Four. Every move is scored
by a solver, so we can measure whether feedback improves move quality versus
chance.

## Files
- `game.py` – rules, solver, and the threat features shown to the neurons
- `neural.py` – everything that touches the CL1 (channel layout, stimulation, readout, feedback)
- `experiment.py` – runs N games and logs each neuron move to `results/*.csv`
- `plot.py` – turns results into `results/summary.png`
- `play.py` – terminal demo, human vs neurons
- `.env` – speeds up the simulator; remove the line on the real device

## Setup (VS Code)
1. Open this folder: File > Open Folder.
2. Open a terminal: Terminal > New Terminal.
3. Create and activate a virtual environment:
   - Mac/Linux: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. Test: `python experiment.py --condition feedback --games 3`

## Running the experiment
    python experiment.py --condition feedback --games 10
    python experiment.py --condition random_feedback --games 10
    python experiment.py --condition none --games 10
    python plot.py

In real time each game takes roughly 15-30 seconds, so 10 games is a few minutes.

## On the night: questions for the hosts
- How do channel numbers map to physical electrode positions? (edit `neural.py`)
- What stimulation amplitudes and burst rates are safe for these cultures?
- Will we run code on the CL1 directly or through Cortical Cloud?
