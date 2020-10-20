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
    str_latex = r'$\sqrt{5}$'
    formula2img(str_latex, r'd:\f1.png', img_size=(3,2), font_size=64)

    str_latex = r'$s=\frac{1-z^{-1}}{T}}$'
    formula2img(str_latex, r'd:\f2.png', img_size=(5, 3), font_size=64)