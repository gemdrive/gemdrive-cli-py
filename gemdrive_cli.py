#!/usr/bin/env python

import sys
import os
from urllib import request
import json
from pprint import pprint
from datetime import datetime
import argparse


def download_file(url, path, gem_data, token):

    if token:
        url += '?access_token=' + token

    try:
        stat = os.stat(path)
    except:
        stat = None
        pass

    size = 0
    if stat:
        size = stat.st_size
        #modTime = datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0).isoformat() + 'Z'
        #print(modTime)

    #print(gem_data['modTime'])

    needs_update = size != gem_data['size']

    if needs_update:
        res = request.urlopen(url)
        with open(path, 'wb') as f:
            while chunk := res.read(4096):
                f.write(chunk)

def download_dir(url, parent_dir, token):

    gem_url = url + 'remfs.json'

    if token:
        gem_url += '?access_token=' + token

    res = request.urlopen(gem_url)
    body = res.read()
    data = json.loads(body)

    try:
        os.makedirs(parent_dir)
    except:
        pass

    for filename in data['children']:
        child = data['children'][filename]

        path = os.path.join(parent_dir, filename)

        print(url + filename)

        if child['type'] == 'file':
            download_file(url + filename, path, child, token)
        else:
            download_dir(url + filename + '/', path, token)

def ls(args):

    url = args.url
    token = args.token

    if url.endswith('/'):
        gem_url = url + 'remfs.json'
    else:
        gem_url = url + '/remfs.json'

    if token:
        gem_url += '?access_token=' + token

    res = request.urlopen(gem_url)
    body = res.read()
    gem_data = json.loads(body)

    print("Filename\tSize")

    for filename in gem_data['children']:
        child = gem_data['children'][filename]
        print("%s\t%d" % (filename, child['size']))

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
        parent_gem_url = '/'.join(url_parts[0:-1]) + '/remfs.json'

        if token:
            parent_gem_url += '?access_token=' + token
        filename = url_parts[-1]

        res = request.urlopen(parent_gem_url)
        body = res.read()
        parent_gem_data = json.loads(body)
        gem_data = parent_gem_data['children'][filename]

        download_file(url, filename, gem_data, token)


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
