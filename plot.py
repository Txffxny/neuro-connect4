"""Plot move quality vs chance for every results/*.csv file.

    python plot.py            # all files in results/
    python plot.py a.csv b.csv
"""
import csv
import glob
import sys
import matplotlib.pyplot as plt

files = sys.argv[1:] or sorted(glob.glob("results/*.csv"))
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
labels, edge, chance = [], [], []

for path in files:
    rows = list(csv.DictReader(open(path)))
    if not rows:
        continue
    good = [int(r["good"]) for r in rows]
    ch = [float(r["chance_good"]) for r in rows]
    window = 10
    rolling = [sum(good[max(0, i - window + 1):i + 1]) / len(good[max(0, i - window + 1):i + 1])
               for i in range(len(good))]
    name = path.split("/")[-1].replace(".csv", "")
    ax1.plot(rolling, label=name)
    labels.append(name)
    edge.append(sum(good) / len(good))
    chance.append(sum(ch) / len(ch))

ax1.set_title("Best-move rate (rolling 10 moves)")
ax1.set_xlabel("Neuron move #")
ax1.set_ylabel("Fraction of best moves")
ax1.legend(fontsize=8)

x = range(len(labels))
ax2.bar([i - 0.2 for i in x], edge, width=0.4, label="Neurons")
ax2.bar([i + 0.2 for i in x], chance, width=0.4, label="Random-player chance")
ax2.set_xticks(list(x))
ax2.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
ax2.set_title("Overall: neurons vs chance")
ax2.legend()

plt.tight_layout()
plt.savefig("results/summary.png", dpi=150)
print("Saved results/summary.png")
plt.show()
