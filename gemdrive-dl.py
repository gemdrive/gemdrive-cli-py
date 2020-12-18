#!/usr/bin/env python3

import os, argparse
from client import GemDriveClient


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


    options = {
        'depth': args.depth,
        'token': args.token,
        'verbose': args.verbose,
        'dry_run': args.dry_run,
        'delete': args.delete,
        'out_dir': args.out_dir,
        'url': args.url,
        'num_workers': args.num_workers,
    }

    client = GemDriveClient(options)
    client.run()
