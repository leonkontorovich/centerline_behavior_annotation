# use imshow to plot several 2D array which contain values from 0 to 7, each array in one figure but with same colormap
#with a dictionary
for array in list_of_arrays:
    ax.imshow(array, cmap='jet')
    # add colorbar
    fig.colorbar(ax=ax)