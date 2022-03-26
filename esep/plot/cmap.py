# -*- coding:utf-8 -*-
"""
-------------------------------------------------------------------------------

                 Project Name : ESEP
                                                                              
                    File Name : cmap.py
                      
                   Start Date : 2021-08-20 14:27
                  
                  Contributor : D.CW
                  
                        Email : dengchuangwu@gmail.com
                                                                              
--------------------------------------------------------------------------------
# Introduction:                                                                #
# Record and save commonly used colors as names related to variables or        #
# data used in actual applications.                                            #
#                                                                              #
#------------------------------------------------------------------------------#
# Note:                                                                        #
#                                                                              #
# Variable Names Format:                                                       #
# ---------------------                                                        #
# cm_(The abbreviation of variable)_(Division[div] of Sequence[seq])           #
#                                                                              #
# Examples:                                                                    #
# --------                                                                     #
# cm_temp_div_18                                                               #
# cm_o3_seq_41                                                                 #
#                                                                              #
#------------------------------------------------------------------------------#
# Variables:                                                                   #
#   cm_temp_div -- A color map used to represent the temperature               #
#                  distribution in a division.                                 #
#   cm_temp_div2 -- A color map used to represent the temperature              #
#                  distribution in a division.                                 #
#   cm_o3_seq -- A color map used to represent the ozone distribution in a     #
#                Sequence.                                                     #
#   cm_gph_seq -- A color map used to represent the geopotential height        #
#                distribution in a Sequence.                                   #
#                                                                              #
#------------------------------------------------------------------------------#
"""

import colorsys

from matplotlib.colors import LinearSegmentedColormap as LineSC, ListedColormap as LineC

cm_temp_div = ['#0000BC', '#0E0EFF', '#2A2AFF', '#4646FF', '#6262FF',
               '#8080FF', '#9C9CFF', '#B8B8FF', '#D4D4FF', '#FFD4D4',
               '#FFB8B8', '#FF9C9C', '#FF7E7E', '#FF6262', '#FF4646',
               '#FF2A2A', '#FF0E0E', '#C00000']
cm_temp_div = LineSC.from_list('cmap', cm_temp_div, 256)

cm_temp_div2 = ['#0006d9', '#194eff', '#3f96ff', '#6dc2ff', '#86d9ff',
                '#9deeff', '#b0f4ff', '#ceffff', '#fffd44', '#ffec00',
                '#ffc400', '#ff9100', '#ff4600', '#ff0000', '#d50000',
                '#9f0000']
cm_temp_div2 = LineSC.from_list('cmap', cm_temp_div2, 256)

cm_o3_seq = [colorsys.hls_to_rgb(i / 255, 150 / 255, 250 / 255) for i in
             range(200, -1, -5)]
cm_o3_seq = LineSC.from_list('cmap', cm_o3_seq, 256)

cm_gph_seq = 'rainbow'

cm_all_div = []
for i in range(160, 240, 5):  # 240-180=60 => 240-160=80
    cm_all_div.append(colorsys.hls_to_rgb(170 / 255, i / 255, 255 / 255))
for i in range(240, 110, -5):  # 340-240=100 => 240-110=130
    cm_all_div.append(colorsys.hls_to_rgb(0 / 255, i / 255, 255 / 255))
cm_all_div = LineC(cm_all_div)

cm_all_div2 = []
for i in range(160, 240, 5):  # 240-180=60 => 240-160=80
    cm_all_div2.append(colorsys.hls_to_rgb(170 / 255, i / 255, 255 / 255))
for i in range(240, 110, -5):  # 340-240=100 => 240-110=130
    cm_all_div2.append(colorsys.hls_to_rgb(0 / 255, i / 255, 255 / 255))
cm_all_div2 = LineC(cm_all_div2)


def _depth_big_area():
    color_ls = ['#FDFECF', '#ED1C24', '#FFFF00', '#22B14C', '#00B0F0', '#00F5FF', '#0000FF', '#0000CD', '#FF00FF',
                '#EDD3ED']
    return cs.LinearSegmentedColormap.from_list('depth_big_area', color_ls, 200)


def cmap_from_act(file, name=None):
    """Import colormap from Adobe Color Table file.

    Parameters:
        file (str): Path to act file.
        name (str): Colormap name. Defaults to filename without extension.

    Returns:
        LinearSegmentedColormap.
    """
    # Extract colormap name from filename.
    if name is None:
        name = os.path.splitext(os.path.basename(file))[0]

    # Read binary file and determine number of colors
    rgb = np.fromfile(file, dtype=np.uint8)
    if rgb.shape[0] >= 770:
        ncolors = rgb[768] * 2 ** 8 + rgb[769]
    else:
        ncolors = 256

    colors = rgb[:ncolors * 3].reshape(ncolors, 3) / 255

    # Create and register colormap...
    cmap = cs.LinearSegmentedColormap.from_list(name, colors, N=ncolors)
    plt.register_cmap(cmap=cmap)  # Register colormap.

    # ... and the reversed colormap.
    cmap_r = cs.LinearSegmentedColormap.from_list(
        name + '_r', np.flipud(colors), N=ncolors)
    plt.register_cmap(cmap=cmap_r)

    return cmap, colors


def gmt_colormap(cpt_path, name=None):
    fd = open(cpt_path)
    color_mode = "RGB"
    # Extract colormap name from filename.
    if name is None:
        name = os.path.splitext(os.path.basename(cpt_path))[0]

    # process file
    x = []
    r = []
    g = []
    b = []
    last_line = None
    for line in fd.readlines():
        lien_split = line.split()

        # skip empty lines
        if not lien_split:
            continue

        # byte comparison is not feasible in python 3
        if (isinstance(line, bytes) and line.decode('utf-8')[0] in ["#",
                                                                    b"#"]) or (
            isinstance(line, str) and line[0] in ["#", b"#"]):
            if lien_split[-1] in ["HSV", b"HSV"]:
                color_mode = "HSV"
                continue
            elif lien_split[-1] in ["RGB", b"RGB"]:
                color_mode = "RGB"
                continue
            else:  # case rogue comment, ignore
                continue

        # skip BFN info
        if lien_split[0] in ["B", b"B", "F", b"F", "N", b"N"]:
            continue

        # parse color vectors
        x.append(float(lien_split[0]))
        r.append(float(lien_split[1]))
        g.append(float(lien_split[2]))
        b.append(float(lien_split[3]))

        # save last row
        last_line = lien_split

    # check if last endrow has the same color, if not, append
    if not ((float(last_line[5]) == r[-1]) and (
        float(last_line[6]) == g[-1]) and (float(last_line[7]) == b[-1])):
        x.append(float(last_line[4]))
        r.append(float(last_line[5]))
        g.append(float(last_line[6]))
        b.append(float(last_line[7]))

    x = np.array(x)
    r = np.array(r)
    g = np.array(g)
    b = np.array(b)

    if color_mode == "HSV":
        for i in range(r.shape[0]):
            # convert HSV to RGB
            rr, gg, bb = colorsys.hsv_to_rgb(r[i] / 360., g[i], b[i])
            r[i] = rr
            g[i] = gg
            b[i] = bb
    elif color_mode == "RGB":
        r /= 255.
        g /= 255.
        b /= 255.

    red = []
    blue = []
    green = []
    x_norm = (x - x[0]) / (x[-1] - x[0])

    # generate cdict
    for i in range(len(x)):
        red.append([x_norm[i], r[i], r[i]])
        green.append([x_norm[i], g[i], g[i]])
        blue.append([x_norm[i], b[i], b[i]])
    cdict = dict(red=red, green=green, blue=blue)
    cmap = cs.LinearSegmentedColormap(name=name, segmentdata=cdict)
    plt.register_cmap(cmap=cmap)
    return cmap


depth_big_area = _depth_big_area()

__all__ = ['depth_big_area']
