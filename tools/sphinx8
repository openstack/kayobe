#!/usr/bin/env python

"""
Sphinx documentation style checker.

This is a very thin wrapper around doc8, that adds support for sphinx-specific
RST directives.

NOTE: We require sphinx>1.5 in order to avoid automatically registering all
directives when any of the directives modules are imported.
"""

import sys

import doc8.main
import sphinx.directives
import sphinx.directives.code
import sphinx.directives.patches


def main():
    # NOTE: Registering sphinx.directives.other causes a failure in parsing
    # later.
    sphinx.directives.setup(None)
    sphinx.directives.code.setup(None)
    sphinx.directives.patches.setup(None)
    return doc8.main.main()


if __name__ == "__main__":
    sys.exit(main())
