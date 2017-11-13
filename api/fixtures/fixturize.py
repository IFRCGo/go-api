#!/usr/bin/env python

"""
Just a simple script to take in a JSON of fields and turn it into Django
fixture data by adding a model field, a primary key, and putting the fields
into a fields entry in the dictionary.
"""
import sys
import json

def main(filename, model):
    with open(filename) as f:
        js = json.loads(f.read())
    newjs = []
    for i, j in enumerate(js):
        newjs.append({"model": model, "pk": i, "fields": j})
    with open(filename, 'w') as f:
        f.write(json.dumps(newjs))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
