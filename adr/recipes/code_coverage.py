"""
Get code coverage information for the given `path` at `rev`. Both arguments are required.

.. code-block:: bash

    adr code_coverage --path <path> --rev <rev>
"""
from __future__ import print_function, absolute_import

from ..recipe import execute_query


def run(args):
    """
    THIS IS PRONE TO DOUBLE COUNTING, AS DIFFERENT TEST CHUNKS COVER COMMON LINES
    AT THE VERY LEAST YOU GET A ROUGH ESTIMATE OF COVERAGE
    """

    result = execute_query('code_coverage')
    output = [result['header']] + result['data']
    return output
