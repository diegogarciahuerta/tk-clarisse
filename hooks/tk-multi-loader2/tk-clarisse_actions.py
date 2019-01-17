# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook that loads defines all the available actions, broken down by publish type. 
"""

import os
from contextlib import contextmanager

import ix
import sgtk
from sgtk.errors import TankError


__author__ = "Diego Garcia Huerta"
__email__ = "diegogh2000@gmail.com"


HookBaseClass = sgtk.get_hook_baseclass()


@contextmanager
def disabled_updates():
    """
    Convenient context that allows to execute a command disabling the
    upating mechanism in Clarisse, which makes things faster.
    """
    clarisse_win = ix.application.get_event_window()
    clarisse_win.set_mouse_cursor(ix.api.Gui.MOUSE_CURSOR_WAIT)
    ix.application.disable()

    try:
        yield
    finally:
        ix.application.enable()
        clarisse_win.set_mouse_cursor(ix.api.Gui.MOUSE_CURSOR_DEFAULT)


class ClarisseActions(HookBaseClass):

    ###########################################################################
    # public interface - to be overridden by deriving classes

    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Returns a list of action instances for a particular publish. This
        method is called each time a user clicks a publish somewhere in the UI.
        The data returned from this hook will be used to populate the actions
        menu for a publish.

        The mapping between Publish types and actions are kept in a different
        place (in the configuration) so at the point when this hook is called,
        the loader app has already established *which* actions are appropriate
        for this object.

        The hook should return at least one action for each item passed in via
        the actions parameter.

        This method needs to return detailed data for those actions, in the
        form of a list of dictionaries, each with name, params, caption and
        description keys.

        Because you are operating on a particular publish, you may tailor the
        output  (caption, tooltip etc) to contain custom information suitable
        for this publish.

        The ui_area parameter is a string and indicates where the publish is to
        be shown.
        - If it will be shown in the main browsing area, "main" is passed.
        - If it will be shown in the details area, "details" is passed.
        - If it will be shown in the history area, "history" is passed.

        Please note that it is perfectly possible to create more than one action
        "instance" for an action!
        You can for example do scene introspectionvif the action passed in 
        is "character_attachment" you may for examplevscan the scene, figure
        out all the nodes where this object can bevattached and return a list
        of action instances: "attach to left hand",v"attach to right hand" etc.
        In this case, when more than  one object isvreturned for an action, use
        the params key to pass additional data into the run_action hook.

        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields. 
        :param actions: List of action strings which have been
                        defined in the app configuration. 
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption 
         and description
        """

        app = self.parent
        app.log_debug(
            "Generate actions called for UI element %s. "
            "Actions: %s. Publish Data: %s"
            % (ui_area, actions, sg_publish_data)
        )

        action_instances = []

        if "reference" in actions:
            action_instances.append(
                {
                    "name": "reference",
                    "params": None,
                    "caption": "Create Reference",
                    "description": ("This will add the item to the current "
                                    "context as a standard reference."),
                }
            )

        if "import" in actions:
            action_instances.append(
                {
                    "name": "import",
                    "params": None,
                    "caption": "Import into Scene",
                    "description": ("This will import the item into the "
                                    "current context."),
                }
            )

        if "texture_node" in actions:
            action_instances.append(
                {
                    "name": "texture_node",
                    "params": None,
                    "caption": "Import Texture Map File",
                    "description": ("Creates a file texture node for the"
                                    "selected item in the current context"),
                }
            )

        if "texture_stream_node" in actions:
            action_instances.append(
                {
                    "name": "texture_stream_node",
                    "params": None,
                    "caption": "Import Texture Streaming Map File",
                    "description": ("Creates a file texture node for the" 
                                    "selected item in the current context"),
                }
            )

        return action_instances

    def execute_multiple_actions(self, actions):
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to
        execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_publish_data: Publish information coming from Shotgun
            params: Parameters passed down from the generate_actions hook.

        .. note::
            This is the default entry point for the hook. It reuses the 
            ``execute_action`` method for backward compatibility with hooks
             written for the previous version of the loader.

        .. note::
            The hook will stop applying the actions on the selection if an
            error is raised midway through.

        :param list actions: Action dictionaries.
        """
        app = self.parent
        for single_action in actions:
            app.log_debug("Single Action: %s" % single_action)
            name = single_action["name"]
            sg_publish_data = single_action["sg_publish_data"]
            params = single_action["params"]

            with disabled_updates():
                self.execute_action(name, params, sg_publish_data)

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.
        
        :param name: Action name string representing one of the items returned
                     by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields.
        :returns: No return value expected.
        """
        app = self.parent
        app.log_debug(
            "Execute action called for action %s. "
            "Parameters: %s. Publish Data: %s" % (name,
                                                  params,
                                                  sg_publish_data)
        )

        # resolve path
        # toolkit uses utf-8 encoded strings internally and Clarisse API 
        # expects unicode so convert the path to ensure filenames containing 
        # complex characters are supported
        path = self.get_publish_path(sg_publish_data).replace(os.path.sep, "/")

        if name == "reference":
            self._create_reference(path, sg_publish_data)

        if name == "import":
            self._do_import(path, sg_publish_data)

        if name == "texture_node":
            self._create_texture_node(path, sg_publish_data)

        if name == "texture_stream_node":
            self._create_texture_node(path, sg_publish_data, stream=True)

    ###########################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the
    # behaviour of things

    def _create_reference(self, path, sg_publish_data):
        """
        Create a reference with the same settings Clarisse would use
        if you used the create settings dialog.
        
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields.
        """
        app = self.parent

        if not os.path.exists(path):
            raise TankError("File not found on disk - '%s'" % path)

        with disabled_updates():
            context = ix.get_current_context()
            ix.reference_file(context, path)

    def _do_import(self, path, sg_publish_data):
        """
        Create a reference with the same settings Clarisse would use
        if you used the create settings dialog.
        
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard
                                publish fields.
        """
        if not os.path.exists(path):
            raise TankError("File not found on disk - '%s'" % path)

        image_extensions = ix.api.ImageIOFileFormat.get_supported_extensions()
        image_extensions = [
            ".%s" % image_extension for image_extension in image_extensions
        ]

        import_scene_extensions = (".lws", ".abc")
        import_geometry_extensions = (".lwo", ".obj")
        import_volume_extensions = ("vdb",)
        import_project_extensions = ix.application.get_project_extension_name()
        import_project_extensions = [
            ext.lower() for ext in import_project_extensions
        ]

        _, extension = os.path.splitext(path)

        with disabled_updates():
            if extension.lower() in import_scene_extensions:
                ix.api.IOHelpers.import_scene(ix.application, path)
            elif extension.lower() in import_project_extensions:
                ix.import_project(path)
            elif extension.lower() in image_extensions:
                ix.import_image(path)
            elif extension.lower() in import_geometry_extensions:
                ix.import_geometry(path)
            elif extension.lower() in import_volume_extensions:
                ix.import_volume(path)

    def _create_texture_node(self, path, sg_publish_data, stream=False):
        """
        Create a file texture node for a texture
        
        :param path:             Path to file.
        :param sg_publish_data:  Shotgun data dictionary with all the standard
                                 publish fields.
        :returns:                The newly created file node
        """
        image_extensions = ix.api.ImageIOFileFormat.get_supported_extensions()
        image_extensions = [
            ".%s".lower() % image_extension
            for image_extension in image_extensions
        ]

        _, extension = os.path.splitext(path)
        if extension.lower() in image_extensions:
            with disabled_updates():
                if not stream:
                    ix.import_map_file(path, "TextureMapFile", "_map")
                else:
                    ix.import_map_file(path, "TextureStreamedMapFile", "_smap")
