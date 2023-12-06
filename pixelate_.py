#!/usr/bin/env python
# -*- coding: utf-8 -*-

# algorithm
#
# a. process options
# b. open image
# c. resize image
#
# 1. take the spaced out pixels
# 2. convert these pixels to dmc colours
# 3. create a new smaller image with these pixels
# 4. quantise the image with the required number of colours
# 5. a new image can then be created with row x column of palette indices
# 6. a new palette can then be created with the dmc 'objects'
# 7. do any extra required cleaning up, for example removing isolated pixels
# 8. svgs can be produced of black/white, colour with symbols, colour only patterns.
# 9. generate the key table

import sys
from PIL import Image
from DMC import DMC
from SVG import SVG
from tqdm import tqdm
from pathlib import Path
from typing import Tuple
from os import makedirs

def get_neighbours(pos, matrix, width: int = 1):
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0

    for i in range(max(0, pos[0] - width), min(rows, pos[0] + width + 1)):
        for j in range(max(0, pos[1] - width), min(cols, pos[1] + width + 1)):
            if not (i == pos[0] and j == pos[1]):
                yield matrix[i][j]

# # a

# # if(len(sys.argv)<3):
# #     print("function requires an input filename, number of colours, stitch count and mode")
# #     sys.exit(0)

# # input_file_name = sys.argv[1]       # input file name, has to be a jpg
# # num_colours = int(sys.argv[2])      # number of colours to use in the pattern
# # count = int(sys.argv[3])            # stitch count, number of stitches in x axis

# def image_resize(image: Image, count: int, new_width: int = 1000) -> Tuple[Image, int]:
#     pixelSize = int(new_width / int(count))
#     new_height = int(new_width * image.size[1] / image.size[0])

#     return image.resize((new_width, new_height), Image.NEAREST), pixelSize


def validate_file(input_file_path):
    if not Path(input_file_path).is_file():
        raise Exception("Input file does not exist")
# TODO: fix annotation problem
def image_resize(image, count: int, new_width: int = 1000) -> Tuple[any, int]:
    pixelSize = int(new_width / int(count))
    new_height = int(new_width * image.size[1] / image.size[0])
    return image.resize((new_width, new_height), Image.NEAREST), pixelSize

def clean_up(x_count: int, y_count: int, svg_pattern: SVG) -> None:
    for x in range(0, x_count):
        for y in range(0, y_count):
            gen = get_neighbours([y, x], svg_pattern)
            neighbours = []
            for n in gen:
                neighbours += [n]
            if svg_pattern[y][x] not in neighbours:
                mode = max(neighbours, key=neighbours.count)
                svg_pattern[y][x] = mode

def calculate_cell_size(x_count: int, y_count: int, col_sym: SVG, blw_nsy: SVG, col_nsy: SVG, svg_cell_size: int = 10) -> int:
    svg_cell_size = 10
    width = x_count * svg_cell_size
    height = y_count * svg_cell_size
    col_sym.prep_for_drawing(width, height)
    col_sym.mid_arrows(svg_cell_size, width, height)
    blw_nsy.prep_for_drawing(width, height)
    blw_nsy.mid_arrows(svg_cell_size, width, height)
    col_nsy.prep_for_drawing(width, height)
    return  svg_cell_size # to allow drawing of midpoint arrows

def main(input_file_path: Path, num_colours: int, size: int, out_directory: Path) -> None:
    if not out_directory.exists():              # size == count
        makedirs(out_directory)

    input_file_path = Path(input_file_path)
    # black_white, minor, symbols
    col_sym = SVG(False, True, True)
    blw_nsy = SVG(True, True, True)
    col_nsy = SVG(False, False, False)
    key = SVG(False, True, True)

    # open image
    if not input_file_path.is_file():
        raise Exception("input file does not exist")
    else:
        im = Image.open(input_file_path)
    # resize image
    im, pixelSize = image_resize(im, size)
    # take the spaced out pixels
    # convert these pixels to dmc colours
    dmc = DMC()
    dmc_spaced = [[dmc.get_dmc_rgb_triple(im.getpixel((x, y))) for x in range(0, im.size[0], pixelSize)] for y in range(0, im.size[1], pixelSize)]

    # create a new smaller image with these pixels
    dmc_image = Image.new('RGB', (len(dmc_spaced[0]), len(dmc_spaced))) #h, w
    dmc_image.putdata([value for row in dmc_spaced for value in row])

    # quantise the image with the required number of colours
    dmc_image = dmc_image.convert('P', palette=Image.ADAPTIVE, colors = num_colours)
    x_count = dmc_image.size[0]
    y_count = dmc_image.size[1]
    # a new image can then be created with row x column of palette indices
    svg_pattern = [[dmc_image.getpixel((x, y)) for x in range(x_count)] for y in range(y_count)]

    # a new palette can then be created with the dmc 'objects'
    palette = dmc_image.getpalette()
    svg_palette = [dmc.get_colour_code_corrected((palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2])) for i in range(num_colours)]

    # do any extra required cleaning up, for example removing isolated pixels
    clean_up(x_count, y_count, svg_pattern)
    # for x in range(0, x_count):
    #     for y in range(0, y_count):
    #         gen = get_neighbours([y, x], svg_pattern)
    #         neighbours = []
    #         for n in gen:
    #             neighbours += [n]
    #         if svg_pattern[y][x] not in neighbours:
    #             mode = max(neighbours, key=neighbours.count)
    #             svg_pattern[y][x] = mode

    # svgs can be produced of black/white, colour with symbols, colour only patterns
    svg_cell_size = calculate_cell_size(x_count, y_count, col_sym, blw_nsy, col_nsy)
    import pdb; pdb.set_trace()
    # svg_cell_size = 10
    # width = x_count * svg_cell_size
    # height = y_count * svg_cell_size
    # col_sym.prep_for_drawing(width, height)
    # col_sym.mid_arrows(svg_cell_size, width, height)
    # blw_nsy.prep_for_drawing(width, height)
    # blw_nsy.mid_arrows(svg_cell_size, width, height)
    # col_nsy.prep_for_drawing(width, height)
    # x = y = svg_cell_size # to allow drawing of midpoint arrows

    for row in tqdm(svg_pattern, total=len(svg_pattern)):
        for colour_index in row:
            col_sym.add_rect(svg_palette, colour_index, x, y, svg_cell_size)
            blw_nsy.add_rect(svg_palette, colour_index, x, y, svg_cell_size)
            col_nsy.add_rect(svg_palette, colour_index, x, y, svg_cell_size)
            x += svg_cell_size
        y += svg_cell_size
        x = svg_cell_size
    blw_nsy.major_gridlines(svg_cell_size, width, height)
    col_sym.major_gridlines(svg_cell_size, width, height)

    # 9

    size = 40
    key.prep_for_drawing(size * 13, size * len(svg_palette))
    x = y = 0
    for i in range(len(svg_palette)):
        key.add_key_colour(x, y, size, i, svg_palette[i])
        y += size

    col_sym.save('col_sym.svg')
    blw_nsy.save('blw_sym.svg')
    col_nsy.save('col_nsy.svg')
    key.save('key.svg')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parse = ArgumentParser("Cross Stitch")
    parse.add_argument("input_file_name", help="input file name, has to be a jpg")
    parse.add_argument("num_colours", type=int, help="number of colours to use in the pattern")
    parse.add_argument("size", type=int, help="stitch count, number of stitches in x axis")
    parse.add_argument("-o","--out-directory", default=Path(Path(__file__).resolve().parent, "output"),
                        type=Path, help="output directory name")
    args = parse.parse_args()

    main(*vars(args).values())