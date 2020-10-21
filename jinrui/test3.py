import matplotlib.pyplot as plt

def formula2img(str_latex, out_file, img_size=(5,3), font_size=16):
    fig = plt.figure(figsize=img_size)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.text(0.5, 0.5, str_latex, fontsize=font_size, verticalalignment='center', horizontalalignment='center')
    plt.savefig(out_file)

if __name__ == '__main__':
    str_latex = r"$\{3x+5y+z \begin{aligned} 7x-2y+4z\ -6x+3y+2z$"
    formula2img(str_latex, r'd:\f1.png', img_size=(18,12), font_size=64)
