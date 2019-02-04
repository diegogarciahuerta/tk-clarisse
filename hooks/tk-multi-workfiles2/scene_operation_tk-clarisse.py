# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import ix

import sgtk
from sgtk.platform.qt import QtGui

HookClass = sgtk.get_hook_baseclass()


__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the
    current scene
    """

    def set_content_directory(self, file_path):
        """
        Set Clarisse Project Content's directory preference $CDIR

        :param file_path:       String
                                The full path to the clarisse project
        """
        content_dir = os.path.join(os.path.dirname(file_path), "Content")
        preferences = ix.application.get_prefs()
        preferences.set_string_value(
            "project", "content_directory", content_dir
        )

    def execute(
        self,
        operation,
        file_path,
        context,
        parent_action,
        file_version,
        read_only,
        **kwargs
    ):
        """
        Main hook entry point

        :param operation:       String
                                Scene operation to perform

        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)

        :param context:         Context
                                The context the file operation is being
                                performed in.

        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as
                                - version_up

        :param file_version:    The version/revision of the file to be opened. 
                                If this is 'None' then the latest version
                                should be opened.

        :param read_only:       Specifies if the file should be opened
                                read-only or not

        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                 file path as a String
                                'reset'        - True if scene was reset to an 
                                                 empty state, otherwise False
                                all others     - None
        """
        app = self.parent

        app.log_debug("-" * 50)
        app.log_debug("operation: %s" % operation)
        app.log_debug("file_path: %s" % file_path)
        app.log_debug("context: %s" % context)
        app.log_debug("parent_action: %s" % parent_action)
        app.log_debug("file_version: %s" % file_version)
        app.log_debug("read_only: %s" % read_only)

        if operation == "current_path":
            # return the current scene path
            return ix.application.get_current_project_filename()

        elif operation == "open":
            ix.application.disable()
            ix.application.load_project(file_path)
            self.set_content_directory(file_path)
            ix.application.enable()

        elif operation == "save":
            file_path = ix.application.get_current_project_filename()
            ix.application.save_project(file_path)
            self.set_content_directory(file_path)
        elif operation == "save_as":
            ix.application.save_project(file_path)
            self.set_content_directory(file_path)

        elif operation == "reset":
            # Propose to save the project if it's modified
            app.log_debug("checking if needing to save...")
            reponse, file_path = ix.check_need_save()

            if reponse.is_yes():
                app.log_debug("saving filename: %s" % file_path)
                ix.application.save_project(file_path)
                self.set_content_directory(file_path)

            if not reponse.is_cancelled():
                # TODO set content directory
                # Probably take the workfile template to figure out where to
                # point it to.

                app.log_debug("creating new project...")
                # create an empty project
                ix.application.new_project()
                # clear and reset all Clarisse windows
                ix.application.reset_windows_layout()
                # load startup scene (define in Clarisse Preferences)
                app.log_debug("loading startup scene...")
                ix.application.load_startup_scene()
            else:
                return False
            return True
