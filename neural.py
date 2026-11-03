"""The bridge between the game and the neurons: encode, read out, give feedback.

Everything that touches the CL1 lives here, so it is the only file you should
need to tweak on the night (channel layout, amplitudes, timings).
"""
import random
import cl
from cl import ChannelSet, StimDesign, BurstDesign

# ---------------------------------------------------------------------------
# Channel layout. Stimulatable channels are 1-62 excluding 4, 7 and 56.
# ASK THE HOSTS how channel numbers map to physical positions on the array:
# ideally input channels sit on one side and output groups on the other.
# ---------------------------------------------------------------------------
STIMMABLE = [c for c in range(1, 63) if c not in (4, 7, 56)]

# 7 columns x 3 threat features = 21 input channels
INPUT_CHANNELS = [[STIMMABLE[col * 3 + f] for f in range(3)] for col in range(7)]
_used = {ch for group in INPUT_CHANNELS for ch in group}

# 7 output groups of 4 channels each; most spikes in a group = that column
_free = [c for c in STIMMABLE if c not in _used]
OUTPUT_GROUPS = [_free[i * 4:(i + 1) * 4] for i in range(7)]
CHANNEL_TO_COLUMN = {ch: col for col, group in enumerate(OUTPUT_GROUPS) for ch in group}

# Feedback goes to every channel we use
FEEDBACK_CHANNELS = sorted(_used | set(CHANNEL_TO_COLUMN))

# ---------------------------------------------------------------------------
# Stimulation settings. Start gentle; ask the Callosum/Frontier team for
# safe amplitude ranges before raising anything.
# ---------------------------------------------------------------------------
PULSE = StimDesign(160, -1.0, 160, 1.0)  # biphasic, 1 uA, 160 us per phase
INPUT_BURST = BurstDesign(5, 50)         # 5 pulses at 50 Hz per active feature
TICKS_PER_SECOND = 100                   # 10 ms ticks
RESPONSE_TICKS = 30                      # read 300 ms of activity after input


def present_board(neurons, features):
    """Stimulate the channels whose threat feature is active, then count
    spikes per output group. Returns a list of 7 spike counts."""
    active = [INPUT_CHANNELS[col][f] for col in range(7) for f in range(3) if features[col][f]]
    counts = [0] * 7
    for tick in neurons.loop(ticks_per_second=TICKS_PER_SECOND, stop_after_ticks=RESPONSE_TICKS):
        if tick.iteration == 0 and active:
            neurons.stim(ChannelSet(*active), PULSE, INPUT_BURST)
        if tick.iteration < 2:
            continue  # skip the first 20 ms: stimulation artefacts, not responses
        for spike in tick.analysis.spikes:
            col = CHANNEL_TO_COLUMN.get(spike.channel)
            if col is not None:
                counts[col] += 1
    return counts


def choose_column(counts, legal):
    """Most active legal column; ties broken at random."""
    top = max(counts[c] for c in legal)
    return random.choice([c for c in legal if counts[c] == top])


def give_feedback(neurons, good):
    """Pong-style feedback. Good move: one predictable synchronised burst on
    all channels. Bad move: unpredictable stimulation on random channels at
    random times. Either way it lasts about one second."""
    ticks = TICKS_PER_SECOND  # one second
    if good:
        for tick in neurons.loop(ticks_per_second=TICKS_PER_SECOND, stop_after_ticks=ticks):
            if tick.iteration == 0:
                neurons.stim(ChannelSet(*FEEDBACK_CHANNELS), PULSE, BurstDesign(10, 100))
    else:
        for tick in neurons.loop(ticks_per_second=TICKS_PER_SECOND, stop_after_ticks=ticks):
            if random.random() < 0.15:
                chans = random.sample(FEEDBACK_CHANNELS, 4)
                neurons.stim(ChannelSet(*chans), PULSE)


def rest(neurons, seconds=0.5):
    for _ in neurons.loop(ticks_per_second=TICKS_PER_SECOND, stop_after_seconds=seconds):
        pass
