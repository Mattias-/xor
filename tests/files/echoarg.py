#!/usr/bin/env python

import sys

if len(sys.argv) < 3:
    sys.exit(555)
for x in sys.argv[2:]:
    (before, _, after) = x.partition('=')
    if before == sys.argv[1]:
        print after
