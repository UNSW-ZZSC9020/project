import matplotlib.pyplot as plt

def setup_plot_style():
    """设置统一的SCI风格图表样式"""
    plt.style.use('classic')
    plt.rcParams.update({
        'figure.figsize': (8, 6),
        'font.family': 'DejaVu Sans',
        'font.size': 10,
        'axes.labelsize': 12,
        'axes.titlesize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'lines.linewidth': 1.5,
        'lines.markersize': 6,
        'legend.fontsize': 10,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'axes.axisbelow': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
        'text.usetex': False
    })