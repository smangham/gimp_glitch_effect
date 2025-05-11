"""
The glitch text code, in a different file so the module can be reloaded for development.
"""
# -*- coding: utf-8 -*-
from random import randrange
from typing import Set

# --- DEBUG ---
# import debugpy
# import inspect
# import os
# import sys

# try:
#     debugpy.listen(("localhost", 5678))
#     debugpy.wait_for_client()
# except:
#     pass

# currentframe = os.path.dirname(inspect.getfile(inspect.currentframe()))
# sys.path.append(currentframe)
# sys.stderr = open(os.path.join(currentframe, "errors.txt"), 'w', buffering=1)
# sys.stdout = open(os.path.join(currentframe, "log.txt"), 'w', buffering=1)
# -------------

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gegl


def glitch_effect(
        image: Gimp.Image,
        glitch_count: int,
        glitch_vertical_size: int,
        glitch_offset_size: int,
        glitch_allow_overlap: bool,
        colour_left: Gegl.Color,
        colour_right: Gegl.Color,
        colour_offset_size: int
):
    """
    Creates a 'glitched' copy of the visible image layers,
    with chunks offset by random amounts, and two-coloured background copies
    slightly offset.

    :param image: The current image.
    :param glitch_count: The number of glitches to generate.
    :param glitch_vertical_size: The vertical size range of the glitches.
    :param glitch_offset_size: The horizontal offset of the glitches.
    :param glitch_allow_overlap: Whether glitches can occur near another glitched block.
    :param colour_left: The colour for the left-hand shifted copy.
    :param colour_right: The colour for the right-size shifted copy.
    :param colour_offset_size: How far the coloured copies are offset.
    """
    image.undo_group_start()
    Gimp.context_push()

    # Create the base layer that will be distorted
    layer_position: int = 0
    layer_base: Gimp.Layer = Gimp.Layer.new_from_visible(
        image=image,
        dest_image=image,
        name="Glitched Layer"
    )
    image.insert_layer(
        layer=layer_base,
        parent=None,
        position=layer_position
    )

    # Hide all the existing layers
    for layer in image.get_layers():
        layer.set_visible(visible=False)

    layer_base.set_visible(visible=True)

    # Select blocks of image and shift them in the x-direction
    x_index_minimum: int = 0
    x_index_maximum: int = image.get_width()
    y_index_minimum: int = 0
    y_index_maximum: int = image.get_height()

    glitched_y_indexes: Set[int] = set()

    for i in range(0,glitch_count):
        glitch_y_size: int = randrange(
            glitch_vertical_size//4, glitch_vertical_size
        )
        glitch_y_index: int = randrange(
            y_index_minimum, y_index_maximum
        )
        glitch_y_indexes = set(
            list(
                range(
                    glitch_y_index - glitch_y_size,
                    glitch_y_index + glitch_y_size*2,
                )
            )
        )

        if glitch_allow_overlap or not glitched_y_indexes.intersection(glitch_y_indexes):
            # Are these y-indexes already 'glitched'? If so, skip this one.
            image.select_rectangle(
                operation=Gimp.ChannelOps.REPLACE,
                x=x_index_minimum,
                y=glitch_y_index,
                width=x_index_maximum,
                height=glitch_y_size
            )
            layer_floating: Gimp.Layer = Gimp.Selection.float(
                image=image,
                drawables=[layer_base],
                offx=randrange(
                    -glitch_offset_size,
                    glitch_offset_size
                ),
                offy=0,
            )
            Gimp.floating_sel_anchor(
                floating_sel=layer_floating
            )

            glitched_y_indexes.update(glitch_y_indexes)

    # Select the base layer, and create shifts of colour off the side
    image.select_item(
        operation=Gimp.ChannelOps.REPLACE,
        item=layer_base
    )
    layer_shift_right: Gimp.Layer = layer_base.copy()
    layer_shift_right.set_name(
        name=f"Shift Layer: {colour_right.get_rgba()}"
    )
    layer_shift_left: Gimp.Layer = layer_base.copy()
    layer_shift_left.set_name(
        name=f"Shift Layer: {colour_left.get_rgba()}"
    )

    image.insert_layer(
        layer=layer_shift_right,
        parent=None,
        position=layer_position+1
    )
    image.insert_layer(
        layer=layer_shift_left,
        parent=None,
        position=layer_position+2
    )

    fraction_hue, fraction_saturation, fraction_lightness, _ = colour_left.get_hsla()
    layer_shift_left.colorize_hsl(
        hue=360*fraction_hue,
        saturation=100*fraction_saturation,
        lightness=fraction_lightness
    )
    fraction_hue, fraction_saturation, fraction_lightness, _ = colour_right.get_hsla()
    layer_shift_right.colorize_hsl(
        hue=360*fraction_hue,
        saturation=100*fraction_saturation,
        lightness=fraction_lightness
    )

    # Replace the black outline with the offset colour
    Gimp.Selection.border(
        image=image,
        radius=1
    )
    Gimp.context_set_foreground(colour_left)
    layer_shift_left.edit_fill(Gimp.FillType.FOREGROUND)

    Gimp.context_set_foreground(colour_right)
    layer_shift_right.edit_fill(Gimp.FillType.FOREGROUND)

    # Shift the offset layers
    _, offset_x, offset_y = layer_base.get_offsets()

    layer_shift_right.set_offsets(
        offx=offset_x+colour_offset_size,
        offy=offset_y
    )
    layer_shift_left.set_offsets(
        offx=offset_x-colour_offset_size,
        offy=offset_y
    )

    # Tidy up
    Gimp.Selection.none(image)
    Gimp.context_pop()
    image.undo_group_end()
    Gimp.displays_flush()
