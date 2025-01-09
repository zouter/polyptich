import matplotlib as mpl

def create_colorbar_horizontal(norm, cmap):
    import matplotlib.pyplot as plt

    fig_colorbar = plt.figure(figsize=(3.0, 0.1))
    ax_colorbar = fig_colorbar.add_axes([0.05, 0.05, 0.5, 0.9])
    mappable = mpl.cm.ScalarMappable(
        norm=norm,
        cmap=cmap,
    )
    colorbar = plt.colorbar(
        mappable, cax=ax_colorbar, orientation="horizontal", extend="both"
    )
    colorbar.set_label("Differential accessibility")
    colorbar.set_ticks(np.log([0.25, 0.5, 1, 2, 4]))
    colorbar.set_ticklabels(["¼", "½", "1", "2", "4"])
    return fig_colorbar
