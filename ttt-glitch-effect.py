#!/usr/bin/env python
# glitch_text.py Release 1
# Created by Tin Tran
# Refer to the below video for instructions on how to create this glitchy effect:
# https://www.youtube.com/watch?v=0Ld22XQDiUI
# Comments directed to http://gimplearn.net
#
# License: GPLv3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY# without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# To view a copy of the GNU General Public License
# visit: http://www.gnu.org/licenses/gpl.html
#
#
# ------------
#| Change Log |
# ------------
# Rel 1: Initial release.
import sys
from typing import List

# --- DEBUG ---
# import debugpy
# import importlib
# import inspect
# import os

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

import glitch_effect


class GlitchEffectPlugin(Gimp.PlugIn):
    """
    Glitchy Effect
    """
    name: str = 'ttt-glitch-effect'
    menu_label: str = "Glitch Effect..."
    menu_path: str = "<Image>/Filters/Distorts"
    documentation: str = "Creates a copy of the visible layers and glitches it out, with mock chromatic abberation and offset chunks."
    dialog_fill: List[str] = [
		'glitch-count',
        'glitch-vertical-size',
        'glitch-offset-size',
        'glitch-allow-overlap',
        'colour-left',
        'colour-right',
        'colour-offset-size',
    ]

    def do_query_procedures(self) -> List[str]:
        """List the procedures in the plugin"""
        return [self.name]

    def do_set_i18n (self, name: str) -> bool:
        """No translation for this plugin"""
        return False

    def do_create_procedure(self, name: str) -> Gimp.ImageProcedure:
        """
        Register the procedure, including arguments.

        :param name: The procedure name, from `do_query_procedures`.
        :return: Each individual procedure.
        """
        # print(f"Creating procedure {name}")
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run,
            None,
        )
        procedure.set_image_types("RGBA")
        procedure.set_menu_label(self.menu_label)
        procedure.add_menu_path(self.menu_path)
        procedure.set_documentation(
            self.documentation,
            self.documentation,
            name
        )
        procedure.set_attribution(
            "Tin Tran/Sam Mangham", "Tin Tran/Sam Mangham", "2018/2025"
        )
        # print(f"Adding arguments")
        procedure.add_int_argument(
            name='glitch-count',
            nick="Number of glitch blocks",
            blurb="Number of glitch blocks. If blocks are barred from overlapping, they may not be generated.",
            min=0, max=50, value=5,
            flags=GObject.ParamFlags.READWRITE
        )
        procedure.add_int_argument(
            name='glitch-vertical-size',
            nick="Vertical size of glitched regions",
            blurb="Glitch vertical heights are evenly distributed from this size down to 1/3 of it.",
            min=1, max=255, value=8,
            flags=GObject.ParamFlags.READWRITE
        )
        procedure.add_int_argument(
            name='glitch-offset-size',
            nick="Horizontal offset of glitched regions",
            blurb="Glitched regions are displaced by up to this many pixels to the left or right.",
            min=1, max=255, value=8,
            flags=GObject.ParamFlags.READWRITE
        )
        procedure.add_boolean_argument(
            name='glitch-allow-overlap',
            nick="Can glitches overlap",
            blurb="Glitches by default prevent other glitches in a neighbouring area equal to their own size.",
            value=False,
            flags=GObject.ParamFlags.READWRITE
        )

		# You have to init Gegl, or you get a silent failure. Delightful!
        Gegl.init(None)
        colour_left: Gegl.Color = Gegl.Color.new('magenta')
        colour_left.set_rgba(1.0, 0.0, 1.0, 1.0)
        colour_right: Gegl.Color = Gegl.Color.new('cyan')
        colour_right.set_rgba(0.0, 1.0, 1.0, 1.0)

        procedure.add_color_argument(
            name='colour-left',
            nick="Left shift colour",
            blurb="Left shift colour",
            has_alpha=True,
            value=colour_left,
            flags=GObject.ParamFlags.READWRITE
        )
        procedure.add_color_argument(
            name='colour-right',
            nick="Right shift colour",
            blurb="Right shift colour",
            has_alpha=True,
            value=colour_right,
            flags=GObject.ParamFlags.READWRITE
        )
        procedure.add_int_argument(
            name='colour-offset-size',
            nick="Size of shift offset",
            blurb="Size of shift offset",
            min=0, max=127, value=2,
            flags=GObject.ParamFlags.READWRITE
        )
        # print(f"Procedure finished")
        return procedure

    def run(
            self: 'GlitchEffectPlugin',
            procedure: Gimp.ImageProcedure,
            run_mode,
            image,
            drawables,
            config,
            run_data
    ):
        """
        The method called when the menu shortcut is run.

        :param procedure: The procedure being called.
        :param run_mode: Whether it's interactive or not.
        :param image: The current image.
        :param drawables: ...not used this?
        :param config: The config values for the procedure.
        :param run_data: ...not used this?
        :return: The return values generated by the procedure.
        """
        # debugpy.wait_for_client()
        # importlib.reload(glitch_effect)

        if run_mode == Gimp.RunMode.INTERACTIVE:
            # print("Starting UI...")
            gi.require_version('Gtk', '3.0')

            GimpUi.init(self.name)
            dialog = GimpUi.ProcedureDialog.new(
                procedure, config, self.menu_label
            )
            dialog.get_label(
                f'{self.name}-docs',
                self.documentation,
                False,
                False,
            )
            dialog.fill([f'{self.name}-docs']+self.dialog_fill)

            if not dialog.run():
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CANCEL, GLib.Error()
                )

        # print("Running swap...")
        try:
            glitch_effect.glitch_effect(
                image=image,
                glitch_count=config.get_property('glitch-count'),
                glitch_vertical_size=config.get_property('glitch-vertical-size'),
                glitch_offset_size=config.get_property('glitch-offset-size'),
                glitch_allow_overlap=config.get_property('glitch-allow-overlap'),
                colour_left=config.get_property('colour-left'),
                colour_right=config.get_property('colour-right'),
                colour_offset_size=config.get_property('colour-offset-size'),
            )
        except Exception as e:
            Gimp.message(f"{e}")
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error()
            )

        # print("Done!")
        # do what you want to do, then, in case of success, return:
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(GlitchEffectPlugin.__gtype__, sys.argv)
