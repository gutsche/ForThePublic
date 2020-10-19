#!/usr/bin/env python

import sys,re

input = open(sys.argv[1]).readlines()
regex = '^\[\]\{(.*)\}\ (.*)'
for line in input:
    matches = re.search(regex, line)
    if matches is not None:
        output = '<!--' + matches.group(1) + '-->\n' + matches.group(2)
    else:
        output = line.strip()
    print(output)
