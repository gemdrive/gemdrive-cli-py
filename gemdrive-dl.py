#!/usr/bin/env python3

import os, argparse, threading, queue, json, math, shutil
from urllib import request
from datetime import datetime

job_queue = queue.Queue(maxsize=8)

def traverse(url, parent_dir, gem_data_in, options):

    max_depth = options['depth']
    token = options['token']

    gem_data = gem_data_in

    if gem_data is None:
        gem_url = url + 'gemdrive/meta.json?depth=' + str(max_depth)

        if token is not None:
            gem_url += '&access_token=' + token

        res = request.urlopen(gem_url)
        body = res.read()
        gem_data = json.loads(body)

    if not os.path.isdir(parent_dir):
        print("Create", parent_dir)
        if options['dry_run']:
            # Early return for dry run because attempts to compare child
            # directories which don't exist will cause exceptions.
            return
        else:
            os.mkdir(parent_dir)

    for child_name in gem_data['children']:
        child = gem_data['children'][child_name]
        child_url = url + child_name
        child_path = os.path.join(parent_dir, child_name)
        is_dir = child_url.endswith('/')
        if is_dir:
            child_gem_data = child
            if 'children' not in child:
                child_gem_data = None

            traverse(child_url, child_path, child_gem_data, options)
        else:
            job_queue.put((child_url, parent_dir, child, options))

    if options['delete']:
        with os.scandir(parent_dir) as it:
            for entry in it:
                name = entry.name
                if entry.is_dir():
                    name += '/'

                if name not in gem_data['children']:
                    item_path = os.path.join(parent_dir, name)
                    print("Delete", item_path)

                    if not options['dry_run']:
                        if entry.is_dir():
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)


def downloader():
    while True:
        url, parent_dir, gem_data, options = job_queue.get()

        handle_file(url, parent_dir, gem_data, options)

        job_queue.task_done()


def handle_file(url, parent_dir, gem_data, options):

    if options['verbose']:
        print(url)

    token = options['token']

    name = os.path.basename(url)
    path = os.path.join(parent_dir, name)

    try:
        stat = os.stat(path)
    except:
        stat = None

    size = 0
    mod_time = ''
    if stat:
        size = stat.st_size
        mod_time = datetime.utcfromtimestamp(stat.st_mtime).replace(microsecond=0).isoformat() + 'Z'

    utc_dt = datetime.strptime(gem_data['modTime'], '%Y-%m-%dT%H:%M:%SZ')
    mtime = math.floor((utc_dt - datetime(1970, 1, 1)).total_seconds())

    needs_update = size != gem_data['size'] or mod_time != gem_data['modTime']

    if needs_update:
        print("Sync", url)

        if not options['dry_run']:
            file_url = url

            if token is not None:
                file_url += '?access_token=' + token

            res = request.urlopen(file_url)
            with open(path, 'wb') as f:
                while True:
                    chunk = res.read(4096)
                    if not chunk:
                        break
                    f.write(chunk)
            stat = os.stat(path)

            if stat.st_size != gem_data['size']:
                print("Sizes don't match", url)

            os.utime(path, (stat.st_atime, mtime))

def dir_name(path):
    return os.path.basename(path[:-1])

if __name__ == '__main__':

    cwd = os.getcwd()

    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='GemDrive directory URL')
    parser.add_argument('--num-workers', type=int, help='Number of worker threads', default=4)
    parser.add_argument('--out-dir', help='Output directory', default=cwd)
    parser.add_argument('--depth', help='Directory tree depth per request', default=8)
    parser.add_argument('--token', help='Access token', default=None)
    parser.add_argument('--verbose', help='Verbose printing', default=False, action='store_true')
    parser.add_argument('--dry-run', help='Enable dry run mode. No changes will be made to destination',
            default=False, action='store_true')
    parser.add_argument('--delete', help="Deletes items in destination that aren't in source", default=False, action='store_true')
    args = parser.parse_args()

    if args.out_dir == cwd:
        args.out_dir = os.path.join(cwd, dir_name(args.url))

    for w in range(args.num_workers):
        threading.Thread(target=downloader, daemon=True).start()

    options = {
        'depth': args.depth,
        'token': args.token,
        'verbose': args.verbose,
        'dry_run': args.dry_run,
        'delete': args.delete,
    }

    traverse(args.url, args.out_dir, None, options)

    job_queue.join()
