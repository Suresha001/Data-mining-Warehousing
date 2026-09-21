import matplotlib.pyplot as plt
import numpy as np

# Set aesthetic styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=300)

metrics = [
    {
        'title': 'Files Opened / Scanned',
        'units': 'Files',
        'full': 144,
        'pruned': 1,
        'reduction': '99.3% Reduction\n(1 vs 144 files)',
        'fmt': '{:,.0f}'
    },
    {
        'title': 'Data Volume Read (I/O)',
        'units': 'Megabytes (MB)',
        'full': 18.47,
        'pruned': 0.15,
        'reduction': '99.2% I/O Reduction\n(153.85 KB vs 18.47 MB)',
        'fmt': '{:,.2f}'
    },
    {
        'title': 'Execution Latency',
        'units': 'Milliseconds (ms)',
        'full': 49.3,
        'pruned': 8.5,
        'reduction': '5.8x Latency Speedup\n(8.5 ms vs 49.3 ms)',
        'fmt': '{:,.1f}'
    }
]

colors = ['#dc3545', '#198754']  # Crimson for Full Scan, Forest Emerald for Pruned

for i, ax in enumerate(axes):
    m = metrics[i]
    x = ['Full Unpartitioned Scan\n(All 144 Partitions)', 'Partition-Pruned Scan\n(store=S01, month=01)']
    y = [m['full'], m['pruned']]
    
    bars = ax.bar(x, y, color=colors, width=0.55, edgecolor='#333333', linewidth=1.2, zorder=3)
    ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{m['fmt'].format(height)} {m['units'].split()[0]}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
    ax.set_title(m['title'], fontsize=13, fontweight='bold', pad=12, color='#1e293b')
    ax.set_ylabel(m['units'], fontsize=11, fontweight='semibold', color='#334155')
    ax.tick_params(axis='x', labelsize=10)
    ax.set_ylim(0, m['full'] * 1.25)
    
    # Add badge for performance gain
    ax.text(0.5, 0.78, m['reduction'], transform=ax.transAxes,
            ha='center', va='center', fontsize=10.5, fontweight='bold',
            color='#0f5132', bbox=dict(boxstyle='round,pad=0.5', facecolor='#d1e7dd', edgecolor='#badbcc', linewidth=1.5))

fig.suptitle('Annapurna Lakehouse — Task A3: Partition Pruning Benchmark Efficiency', 
             fontsize=16, fontweight='bold', y=1.03, color='#0f172a')
plt.tight_layout()
plt.savefig('screenshots/partition_pruning_benchmark.png', bbox_inches='tight')
print("Saved screenshots/partition_pruning_benchmark.png successfully!")
