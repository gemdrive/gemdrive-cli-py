#!/usr/bin/env python

import sys
import os
from urllib import request
from urllib.parse import urlparse 
from datetime import datetime
import argparse
import math


def download_file(url, path, gem_data, token):

    if token:
        url += '?access_token=' + token

    try:
        stat = os.stat(path)
    except:
        stat = None
        pass

    size = 0
    mod_time = ''
    if stat:
        size = stat.st_size
        mod_time = datetime.utcfromtimestamp(stat.st_mtime).replace(microsecond=0).isoformat() + 'Z'

    utc_dt = datetime.strptime(gem_data['modTime'], '%Y-%m-%dT%H:%M:%SZ')
    mtime = math.floor((utc_dt - datetime(1970, 1, 1)).total_seconds())

    needs_update = size != gem_data['size'] or mod_time != gem_data['modTime']

    if needs_update:
        res = request.urlopen(url)
        with open(path, 'wb') as f:
            while chunk := res.read(4096):
                f.write(chunk)
        stat = os.stat(path)
        os.utime(path, (stat.st_atime, mtime))

def download_dir(url, parent_dir, token):

    gem_url = url + '.gemdrive-ls.tsv'

    if token:
        gem_url += '?access_token=' + token

    res = request.urlopen(gem_url)
    body = res.read()
    gem_data = parse_gemdata(body.decode('utf-8'))

    try:
        os.makedirs(parent_dir)
    except:
        pass

    for filename in gem_data:
        item = gem_data[filename]

        path = os.path.join(parent_dir, filename)

        print(url + filename)

        if filename.endswith('/'):
            download_dir(url + filename, path, token)
        else:
            download_file(url + filename, path, item, token)

def ls(args):

    url = args.url
    token = args.token

    gem_url = url + '.gemdrive-ls.tsv'

    if token:
        gem_url += '?access_token=' + token

    res = request.urlopen(gem_url)
    body = res.read()
    gem_data = parse_gemdata(body.decode('utf-8'))

    print("Filename\tModTime\tSize")

    for name in gem_data:
        item = gem_data[name]
        print("{}\t{}\t{}".format(name, item['modTime'], item['size']))

def sync(args):

    url = args.url
    token = args.token

    if args.out_dir:
        out_dir = args.out_dir 
    else:
        out_dir = os.getcwd()

    if url.endswith('/'):
        download_dir(url, out_dir, token)
    else:
        url_parts = url.split('/')
        parent_dir_url = '/'.join(url_parts[0:-1]) + '/'

        parent_gem_url = parent_dir_url + '.gemdrive-ls.tsv'

        if token:
            parent_gem_url += '?access_token=' + token
        filename = url_parts[-1]

        res = request.urlopen(parent_gem_url)
        body = res.read()
        parent_gem_data = parse_gemdata(body.decode('utf-8'))

        gem_data = parent_gem_data[filename]

        download_file(url, filename, gem_data, token)


def parse_gemdata(tsv):
    lines = tsv.splitlines()
    gem_data = {}

    for line in lines:
        columns = str(line).split('\t')
        name = columns[0]
        gem_data[name] = {
            'modTime': columns[1],
            'size': int(columns[2]),
        }

    return gem_data


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('command', help='Command')
    parser.add_argument('url', help='GemDrive URI')
    parser.add_argument('--token')
    parser.add_argument('--out_dir')
    args = parser.parse_args()

    if args.command == 'ls':
        ls(args)
    elif args.command == 'sync':
        sync(args)
    else:
        print("Unrecognized command: " + args.command)
        sys.exit(1)
