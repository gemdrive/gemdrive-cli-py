#!/usr/bin/env python3

import sys, json, argparse
from urllib import request

parser = argparse.ArgumentParser()
parser.add_argument('url', help='GemDrive directory URL')
parser.add_argument('--token', help='Access token', default=None)
args = parser.parse_args()

is_dir = args.url.endswith('/')

if not args.url.startswith('http'):
    args.url = 'https://' + args.url

if is_dir:
    url = args.url+ '/gemdrive/meta.json'
    if args.token is not None:
        url += '?access_token=' + args.token

    res = request.urlopen(url)
    body = res.read()
    gem_data = json.loads(body)

    for child_name in gem_data['children']:
        is_dir = child_name.endswith('/')

        out = child_name

        if not is_dir:
            child = gem_data['children'][child_name]
            out += "\t{}\t{}".format(child['size'], child['modTime'])

        print(out)
else:
    url = args.url
    if args.token is not None:
        url += '?access_token=' + args.token

    res = request.urlopen(url)

    try:
        while True:
            chunk = res.read(4096)
            if not chunk:
                break
            sys.stdout.buffer.write(chunk)
    except KeyboardInterrupt:
        sys.stderr.write("Aborting")
