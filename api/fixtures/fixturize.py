#!/usr/bin/env python

"""
Script to read in a CSV file and create a Django fixture file from it.
This script was used to create the Countries.json and DisasterTypes.json
files from CSV input files.
Arguments:
    - filename is the name of the input CSV file
    - model is the Django model name (e.g., api.Country)
    - pk is the name of the column containing the primary key
    - fields is a list of arguments with the form key=value.
        key is the column name in the CSV file
        value is the field name in the Django model
"""
import os
import sys
import csv
import json
import argparse


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
