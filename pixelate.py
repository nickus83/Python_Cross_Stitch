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
from typing import Tuple, List
from os import makedirs

COL_SYM = SVG(False, True, True)
BLW_NSY = SVG(True, True, True)
COL_NSY = SVG(False, False, False)
KEY = SVG(False, True, True)
KEY_SIZE_WIDTH = 13

def get_neighbours(pos, matrix):
    """
    Retrieves the neighboring elements of a given position in a matrix.

    Parameters:
        pos (tuple): The position (row, column) of the element in the matrix.
        matrix (list): The matrix containing the elements.

    Yields:
        object: The neighboring elements of the given position.

    Example:
        >>> matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> list(get_neighbours((1, 1), matrix))
        [1, 2, 3, 4, 6, 7, 8, 9]
    """
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    width = 1
    for i in range(max(0, pos[0] - width), min(rows, pos[0] + width + 1)):
        for j in range(max(0, pos[1] - width), min(cols, pos[1] + width + 1)):
            if not (i == pos[0] and j == pos[1]):
                yield matrix[i][j]

def image_resize(image: Image, size: int, new_width: int = 1000) -> Tuple[any, int]:
    """
    Resizes an image to a specified size, while maintaining its aspect ratio.

    Parameters:
    - image: The image to be resized. (type: Image)
    - size: The desired size of the image. (type: int)
    - new_width: The new width of the image. Default is 1000. (type: int)

    Returns:
    - A tuple containing the resized image and the size of each pixel. (type: Tuple[any, int])
    """
    pixelSize = int(new_width / int(size))
    new_height = int(new_width * image.size[1] / image.size[0])
    image = image.resize((new_width, new_height), Image.NEAREST)
    return image, pixelSize

def get_dmc_image(dmc_spaced: List[List[Tuple[int, int, int]]], num_colours: int) -> Image:
    """
    Generates a DMC image from a given DMC spaced image and the desired number of colors.

    Args:
        dmc_spaced (List[List[Tuple[int, int, int]]]): The DMC spaced image represented as a list of lists of RGB tuples.
        num_colours (int): The desired number of colors in the DMC image.

    Returns:
        Image: The generated DMC image.

    """
    dmc_image = Image.new('RGB', (len(dmc_spaced[0]), len(dmc_spaced))) #h, w
    dmc_image.putdata([value for row in dmc_spaced for value in row])
    dmc_image = dmc_image.convert('P', palette=Image.ADAPTIVE, colors = num_colours)

    return dmc_image

def update_svg_pattern(x_count: int, y_count: int, svg_pattern: SVG) -> None:
    """
    Update the SVG pattern by filling in missing values with the mode of its neighbors.

    Args:
        x_count (int): The number of columns in the SVG pattern.
        y_count (int): The number of rows in the SVG pattern.
        svg_pattern (SVG): The SVG pattern to be updated.

    Returns:
        None: This function modifies the `svg_pattern` in place and does not return anything.
    """
    for x in range(0, x_count):
            for y in range(0, y_count):
                gen = get_neighbours([y, x], svg_pattern)
                neighbours = []
                for n in gen:
                    neighbours += [n]
                if svg_pattern[y][x] not in neighbours:
                    mode = max(neighbours, key=neighbours.count)
                    svg_pattern[y][x] = mode

# c
def main(input_file_path: Path, num_colours: int, size: int, out_directory: Path,
        svg_cell_size: int, key_size: int) -> None:
    """
    Generates a set of SVG files based on the input image file.

    Args:
        input_file_path (Path): The path to the input image file.
        num_colours (int): The number of colors to quantize the image to.
        size (int): The size to resize the image to.
        out_directory (Path): The directory to save the generated SVG files to.
        svg_cell_size (int): The size of each cell in the SVG files.
        key_size (int): The size of the key table in the SVG files.

    Returns:
        None: This function does not return anything.
    """
    if not out_directory.exists():
        makedirs(out_directory)

    # open image
    image_file_path = Path(input_file_path)
    if not image_file_path.is_file():
        raise Exception("input file does not exist")
    else:
        image = Image.open(image_file_path)

    image, pixelSize = image_resize(image, size)

    # take the spaced out pixels
    # convert these pixels to dmc colours
    dmc = DMC()
    dmc_spaced = [
        [
            dmc.get_dmc_rgb_triple(image.getpixel((x, y)))
            for x in range(0, image.size[0], pixelSize)
        ]
        for y in range(0, image.size[1], pixelSize)
    ]

    # quantise the image with the required number of colours
    #  a new image can then be created with row x column of palette indices
    dmc_image = get_dmc_image(dmc_spaced, num_colours)
    x_count = dmc_image.size[0]
    y_count = dmc_image.size[1]

    svg_pattern = [[dmc_image.getpixel((x, y)) for x in range(x_count)] for y in range(y_count)]

    # a new palette can then be created with the dmc 'objects'
    palette = dmc_image.getpalette()
    svg_palette = [
        dmc.get_colour_code_corrected((palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]))
        for i in range(num_colours)
    ]

    # do any extra required cleaning up, for example removing isolated pixels
    update_svg_pattern(x_count, y_count, svg_pattern)

    # svgs can be produced of black/white, colour with symbols, colour only patterns.
    width = x_count * svg_cell_size
    height = y_count * svg_cell_size

    COL_SYM.prep_for_drawing(width, height)
    COL_SYM.mid_arrows(svg_cell_size, width, height)
    BLW_NSY.prep_for_drawing(width, height)
    BLW_NSY.mid_arrows(svg_cell_size, width, height)
    COL_NSY.prep_for_drawing(width, height)

    x = y = svg_cell_size # to allow drawing of midpoint arrows

    for row in svg_pattern:
        for colour_index in row:
            COL_SYM.add_rect(svg_palette, colour_index, x, y, svg_cell_size)
            BLW_NSY.add_rect(svg_palette, colour_index, x, y, svg_cell_size)
            COL_NSY.add_rect(svg_palette, colour_index, x, y, svg_cell_size)
            x += svg_cell_size
        y += svg_cell_size
        x = svg_cell_size
    BLW_NSY.major_gridlines(svg_cell_size, width, height)
    COL_SYM.major_gridlines(svg_cell_size, width, height)


    # generate the key table
    KEY.prep_for_drawing(key_size * KEY_SIZE_WIDTH, key_size * len(svg_palette))
    x_count = y_count = 0
    for idx in range(len(svg_palette)):
        KEY.add_key_colour(x_count, y_count, key_size, idx, svg_palette[idx])
        y_count += key_size

    COL_SYM.save(Path(out_directory, 'col_sym.svg'))
    BLW_NSY.save(Path(out_directory, 'blw_sym.svg'))
    COL_NSY.save(Path(out_directory, 'col_nsy.svg'))
    KEY.save(Path(out_directory, 'key.svg'))

if __name__ == '__main__':
    from argparse import ArgumentParser
    parse = ArgumentParser("Cross Stitch")
    parse.add_argument("input_file_name", help="input file name, has to be a jpg")
    parse.add_argument("num_colours", type=int, help="number of colours to use in the pattern")
    parse.add_argument("size", type=int, help="stitch count, number of stitches in x axis")
    parse.add_argument("-o","--out-directory", default=Path(Path(__file__).resolve().parent, "output"),
                        type=Path, help="output directory name")
    parse.add_argument("-s", "--svg-cell-size", default=10, type=int, help="svg cell size")
    parse.add_argument("-k", "--key-size", default=40, type=int, help="key size")
    args = parse.parse_args()

    main(*vars(args).values())