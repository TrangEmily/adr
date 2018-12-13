from __future__ import print_function, absolute_import

import importlib
import logging
import os
from .query import run_query, load_query_context
from argparse import ArgumentParser, Namespace
from adr.formatter import all_formatters
from .errors import MissingDataError
from adr import context
log = logging.getLogger('adr')
here = os.path.abspath(os.path.dirname(__file__))

RECIPE_DIR = os.path.join(here, 'recipes')


def set_config(config):
    global G_CONFIG
    G_CONFIG = config


def set_query_context(query_args):
    global G_CONTEXT
    G_CONTEXT = query_args


def execute_query(query_name, override_context=None):
    """
    Set the query context, then run query
    Args:
        query_name (str): name of query
        override_context (dict): updated context from previous query
    Returns: (str)

    """

    if not override_context:
        override_context = G_CONTEXT
    else:
        if type(override_context) is not dict:
            override_context = vars(override_context)
        for key, value in G_CONTEXT.items():
            if not (key in override_context):
                override_context[key] = value
    return run_query(query_name, G_CONFIG, **override_context)


class RecipeParser(ArgumentParser):

    def __init__(self, definitions):
        ArgumentParser.__init__(self)

        for name, definition in definitions.items():
            if isinstance(definition, dict):
                self.add_argument(name, **definition)
            elif len(definition) >= 2:
                # Set destination from name
                definition[1]['dest'] = name
                self.add_argument(*definition[0], **definition[1])
            else:
                raise AttributeError("Definition of {} should be list of length 2".format(name))


def run_recipe(recipe, args, config):
    """Given a recipe, calls the appropriate query and returns the result.

    The provided recipe name is used to make a call to the modules.

    Args:
        recipe (str): name of the recipe to be run.
        args (list): remainder arguments that were unparsed.
        config (Configuration): config object.

    Returns:
        output (str): output after formatted.

    """
    modname = '.recipes.{}'.format(recipe)
    mod = importlib.import_module(modname, package='adr')

    # try to extract name of query and run contexts automatically from run function
    queries, run_contexts = context.extract_arguments(mod.run, "execute_query")

    # Get name of queries and/or run context definitions by function
    if hasattr(mod, 'get_queries'):
        queries = mod.get_queries()
    if hasattr(mod, 'get_run_contexts'):
        run_contexts = mod.get_run_contexts()

    query_context_def = {}
    for query_name in set(queries):
        query_contexts = load_query_context(query_name)
        query_context_def.update(query_contexts)

    run_context_def = context.get_context_definitions(run_contexts)

    recipe_context_def = {}
    # get run_context first so that the value of context in run_context has higher priority
    recipe_context_def.update(run_context_def)
    recipe_context_def.update(query_context_def)

    # get value of query parameters and post-processing parameters
    parsed_args = RecipeParser(recipe_context_def).parse_args(args)
    set_config(config)

    # Split recipe_args into query_args and recipe_args while keep --help works correctly
    parsed_args_items = vars(parsed_args).items()
    query_args = {k: v for k, v in parsed_args_items if k in query_context_def}
    run_args = {k: v for k, v in parsed_args_items if k in run_context_def}

    set_query_context(query_args)

    try:
        output = mod.run(Namespace(**run_args))
    except MissingDataError:
        return "ActiveData didn\'t return any data."

    if isinstance(config.fmt, str):
        fmt = all_formatters[config.fmt]

    log.debug("Result:")
    return fmt(output)
