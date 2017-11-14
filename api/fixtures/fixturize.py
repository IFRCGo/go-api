#!/usr/bin/env python

"""
Script to read in a CSV file and create a Django fixture file from it
"""
import os
import sys
import csv
import json
import argparse


class KeyValuePair(argparse.Action):
    """ Custom action for getting key=value pairs from argparse """
    def __call__(self, parser, namespace, values, option_string=None):
        for val in values:
            n, v = val.split('=')
            setattr(namespace, n, v)


def csv_to_json(input):
    reader = csv.reader(input, delimiter=',', quotechar='"')
    records = []
    for i, row in enumerate(reader):
        if i == 0:
            header = row
        else:
            d = {header[i]: l for i, l in enumerate(row)}
            records.append(d)
    return records


def main(filename, model, fields, pk=None):
    with open(filename) as f:
        records = csv_to_json(f.readlines())
    new_records = []
    for i, record in enumerate(records):
        key = i if pk is None else record[pk]
        flds = {}
        for f in fields:
            parts = f.split('=')
            if len(parts) == 1:
                flds.update({f: record[f]})
            elif len(parts) == 2:
                flds.update({parts[1]: record[parts[0]]})
        new_records.append({"model": model, "pk": key, "fields": flds})
    fout = os.path.splitext(filename)[0] + '.json'
    with open(fout, 'w') as f:
        f.write(json.dumps(new_records))


def parse_args(args):
    """ Parse command line arguments """
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description='IFRC fixturize CSV data', formatter_class=dhf)
    parser.add_argument('filename', help='CSV filename')
    parser.add_argument('model', help='Model name (e.g., api.Country)')
    parser.add_argument('fields', nargs='*', help='Fields to keep')
    parser.add_argument('--pk', help='Primary key (auto-increment from 0 if None)', default=None)
    return vars(parser.parse_args(args))


def cli():
    """ Run a CLI, parsing args from command line """
    args = parse_args(sys.argv[1:])
    main(**args)


if __name__ == "__main__":
    cli()