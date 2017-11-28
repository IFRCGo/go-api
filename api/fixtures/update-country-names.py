#!/usr/bin/env python

"""
Script to translate DisasterType fixtures text from
what comes out of DMIS, to what's being used now.
"""

import sys
import json
import argparse
from dtype_map import DISASTER_TYPE_MAPPING


def main(input, output):
    with open(input) as f:
        records = json.load(f)

    # replace old keys with new, and dedupe
    new_records = []
    for fixture in records:
        key = fixture['fields']['name']

        if key in DISASTER_TYPE_MAPPING:
            fixture['fields']['name'] = DISASTER_TYPE_MAPPING[key]

        exists = len([f for f in new_records if f['fields']['name'] == fixture['fields']['name']])
        if not exists:
            new_records.append(fixture)

    with open(output, 'w') as o:
        o.write(json.dumps(new_records, indent=2))


def parse_args(args):
    """ Parse command line arguments """
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description='Convert disaster type fixture', formatter_class=dhf)
    parser.add_argument('input', help='DisasterType input filename (json)')
    parser.add_argument('output', help='Reformatted DisasterType output filename')
    return vars(parser.parse_args(args))


def cli():
    """ Run a CLI, parsing args from command line """
    args = parse_args(sys.argv[1:])
    main(**args)


if __name__ == "__main__":
    cli()
