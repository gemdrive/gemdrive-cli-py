import sys
import os
from urllib import request
import json
from pprint import pprint


def download_file(url, path, gem_data):

    try:
        stat = os.stat(path)
        size = stat.st_size
    except:
        size = 0

    needs_update = size != gem_data['size']

    if needs_update:
        res = request.urlopen(url)
        with open(path, 'wb') as f:
            while chunk := res.read(4096):
                f.write(chunk)

def download_dir(url, parent_dir):
    res = request.urlopen(url + 'remfs.json')

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
            download_file(url + filename, path, child)
        else:
            download_dir(url + filename + '/', path)


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Invalid args")
        sys.exit(1)

    url = sys.argv[1]

    d = os.getcwd()

    if url.endswith('/'):
        download_dir(url, d)
    else:
        url_parts = url.split('/')
        parent_gem_url = '/'.join(url_parts[0:-1]) + '/remfs.json'
        filename = url_parts[-1]

        res = request.urlopen(parent_gem_url)
        body = res.read()
        parent_gem_data = json.loads(body)
        gem_data = parent_gem_data['children'][filename]

        download_file(url, filename, gem_data)
