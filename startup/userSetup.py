# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
This file is loaded automatically by Clarisse at startup
It sets up the Toolkit context and prepares the tk-clarisse engine.
"""

import os
from contextlib import contextmanager

import ix


__author__ = "Diego Garcia Huerta"
__contact__ = "https://www.linkedin.com/in/diegogh/"


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


def display_error(msg):
    ix.application.log_error("Shotgun Error | Clarisse engine | %s " % msg)


def display_warning(msg):
    ix.application.log_warning("Shotgun Warning | Clarisse engine | %s " % msg)


def display_info(msg):
    ix.application.log_info("Shotgun Info | Clarisse engine | %s " % msg)


def start_toolkit_classic():
    """
    Parse enviornment variables for an engine name and
    serialized Context to use to startup Toolkit and
    the tk-clarisse engine and environment.
    """
    import sgtk

    logger = sgtk.LogManager.get_logger(__name__)

    logger.debug("Launching toolkit in classic mode.")

    # Get the name of the engine to start from the environement
    env_engine = os.environ.get("SGTK_ENGINE")
    if not env_engine:
        msg = "Shotgun: Missing required environment variable SGTK_ENGINE."
        display_error(msg)
        return

    # Get the context load from the environment.
    env_context = os.environ.get("SGTK_CONTEXT")
    if not env_context:
        msg = "Shotgun: Missing required environment variable SGTK_CONTEXT."
        display_error(msg)
        return
    try:
        # Deserialize the environment context
        context = sgtk.context.deserialize(env_context)
    except Exception as e:
        msg = "Shotgun: Could not create context! Shotgun Pipeline Toolkit"
        msg += " will be disabled. Details: %s" % e
        display_error(msg)
        return

    try:
        # Start up the toolkit engine from the environment data
        logger.debug(
            "Launching engine instance '%s' for context %s"
            % (env_engine, env_context)
        )
        engine = sgtk.platform.start_engine(env_engine, context.sgtk, context)
    except Exception as e:
        msg = "Shotgun: Could not start engine. Details: %s" % e
        display_error(msg)
        return


def start_toolkit():
    """
    Import Toolkit and start up a tk-clarisse engine based on
    environment variables.
    """

    # Verify sgtk can be loaded.
    try:
        import sgtk
    except Exception as e:
        msg = "Shotgun: Could not import sgtk! Disabling for now: %s" % e
        display_error(msg)
        return

    # start up toolkit logging to file
    sgtk.LogManager().initialize_base_file_handler("tk-clarisse")

    # Rely on the classic boostrapping method
    start_toolkit_classic()

    # Check if a file was specified to open and open it.
    file_to_open = os.environ.get("SGTK_FILE_TO_OPEN")
    if file_to_open:
        msg = "Shotgun: Opening '%s'..." % file_to_open
        display_info(msg)

        with disabled_updates():
            ix.application.load_project(file_to_open)
            content_dir = os.path.join(os.path.dirname(file_to_open), "Content")
            preferences = ix.application.get_prefs()
            preferences.set_string_value(
                "project", "content_directory", content_dir
            )
            

    # Clean up temp env variables.
    del_vars = ["SGTK_ENGINE", "SGTK_CONTEXT", "SGTK_FILE_TO_OPEN"]
    for var in del_vars:
        if var in os.environ:
            del os.environ[var]


# Fire up Toolkit and the environment engine when there's time.
start_toolkit()
