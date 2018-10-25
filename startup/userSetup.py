# ------------------------------------------------------------------------------
# Copyright (C) 2018 Diego Garcia Huerta - All Rights Reserved
#
# CONFIDENTIAL AND PROPRIETARY
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Diego Garcia Huerta <diegogh2000@gmail.com>. October 2018
# ------------------------------------------------------------------------------

"""
This file is loaded automatically by Clarisse at startup
It sets up the Toolkit context and prepares the tk-clarisse engine.
"""

import os
import ix


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
    except Exception, e:
        msg = "Shotgun: Could not create context! Shotgun Pipeline Toolkit will be disabled. Details: %s" % e
        display_error(msg)
        return

    try:
        # Start up the toolkit engine from the environment data
        logger.debug("Launching engine instance '%s' for context %s" % (env_engine, env_context))
        engine = sgtk.platform.start_engine(env_engine, context.sgtk, context)
    except Exception, e:
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
    except Exception, e:
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

        ix.application.disable()
        ix.application.load_project(file_to_open)
        content_dir = os.path.join(os.path.dirname(file_to_open), "Content")
        preferences = ix.application.get_prefs()
        preferences.set_string_value("project",
                                    "content_directory",
                                    content_dir)
        ix.application.enable()

    # Clean up temp env variables.
    del_vars = [
        "SGTK_ENGINE", "SGTK_CONTEXT", "SGTK_FILE_TO_OPEN",
    ]
    for var in del_vars:
        if var in os.environ:
            del os.environ[var]


# Fire up Toolkit and the environment engine when there's time.
start_toolkit()
