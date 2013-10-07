#!/usr/bin/env python

import textwrap

class MattsWebTools:

    def truncate(self, text, max_size):
        if len(text) <= max_size:
            return text
        return textwrap.wrap(text, max_size-3)[0] + "..."