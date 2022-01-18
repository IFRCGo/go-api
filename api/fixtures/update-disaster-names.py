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
    # also keep track of what old primary keys map with new
    pk_map = {}
    for fixture in records:
        key = fixture['fields']['name']

        if key in DISASTER_TYPE_MAPPING:
            fixture['fields']['name'] = DISASTER_TYPE_MAPPING[key]

        exists = [f for f in new_records if f['fields']['name'] == fixture['fields']['name']]
        old_pk = str(fixture['pk'])
        if len(exists):
            pk_map[old_pk] = exists[0]['pk']
        else:
            new_records.append(fixture)
            pk_map[old_pk] = old_pk

    with open('%s.json' % output, 'w') as o:
        o.write(json.dumps(new_records, indent=2))

    with open('%s-pks.json' % output, 'w') as o:
        o.write(json.dumps(pk_map, indent=2))


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
