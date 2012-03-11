#!/usr/bin/env python

import os
import sys
import datetime
import argparse


def versions(dirpath, time_format=None):
    versions = []
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if not os.path.isdir(filepath):
            continue
        try:
            datetime.datetime.strptime(filename, time_format)
        except ValueError:
            continue
        is_tmp = not os.path.exists(os.path.join(filepath, '.fabdeploy'))
        versions.append((filename, is_tmp))
    versions.sort(reverse=True)
    return versions


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dirpath', type=str)
    parser.add_argument('time_format', type=str)
    args = parser.parse_args()

    v = versions(args.dirpath, time_format=args.time_format)
    sys.stdout.write(repr(v))
