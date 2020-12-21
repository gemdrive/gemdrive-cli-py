import os, threading, queue, json, math, shutil, stat
from urllib import request
from datetime import datetime


class GemDriveClient():

    def __init__(self, **kwargs):

        self.options = kwargs
        self.job_queue = queue.Queue(maxsize=8)

        for w in range(kwargs['num_workers']):
            threading.Thread(target=self.downloader, daemon=True).start()

    def sync(self, gemdrive_url, fs_dir):
        self.traverse(gemdrive_url, fs_dir, None)
        self.job_queue.join()

    def traverse(self, url, parent_dir, gem_data_in):

        max_depth = self.options['depth']
        token = self.options['token']

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
            if self.options['dry_run']:
                # Early return for dry run because attempts to compare child
                # directories which don't exist will cause exceptions.
                return
            else:
                os.mkdir(parent_dir)

        if 'children' not in gem_data:
            return

        for child_name in gem_data['children']:
            child = gem_data['children'][child_name]
            child_url = url + child_name
            child_path = os.path.join(parent_dir, child_name)
            is_dir = child_url.endswith('/')
            if is_dir:
                child_gem_data = child
                if 'children' not in child:
                    child_gem_data = None

                self.traverse(child_url, child_path, child_gem_data)
            else:
                self.job_queue.put((child_url, parent_dir, child))

        if self.options['delete']:
            with os.scandir(parent_dir) as it:
                for entry in it:
                    name = entry.name
                    if entry.is_dir():
                        name += '/'

                    if name not in gem_data['children']:
                        item_path = os.path.join(parent_dir, name)
                        print("Delete", item_path)

                        if not self.options['dry_run']:
                            if entry.is_dir():
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)

    def downloader(self):
        while True:
            url, parent_dir, gem_data = self.job_queue.get()

            self.handle_file(url, parent_dir, gem_data)

            self.job_queue.task_done()


    def handle_file(self, url, parent_dir, gem_data):

        if self.options['verbose']:
            print(url)

        token = self.options['token']

        name = os.path.basename(url)
        path = os.path.join(parent_dir, name)

        try:
            stats = os.stat(path)
        except:
            stats = None

        size = 0
        mod_time = ''
        dest_is_exe = False
        if stats:
            size = stats.st_size
            mod_time = datetime.utcfromtimestamp(stats.st_mtime).replace(microsecond=0).isoformat() + 'Z'
            dest_is_exe = stats.st_mode & 0o111 != 0


        utc_dt = datetime.strptime(gem_data['modTime'], '%Y-%m-%dT%H:%M:%SZ')
        mtime = math.floor((utc_dt - datetime(1970, 1, 1)).total_seconds())

        needs_update = size != gem_data['size'] or mod_time != gem_data['modTime']

        src_is_exe = 'isExecutable' in gem_data and gem_data['isExecutable']

        if  src_is_exe != dest_is_exe:
            needs_update = True

        if needs_update:
            print("Sync", url)

            if not self.options['dry_run']:
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
                stats = os.stat(path)

                if stats.st_size != gem_data['size']:
                    print("Sizes don't match", url)

                os.utime(path, (stats.st_atime, mtime))

                if src_is_exe and not dest_is_exe:
                    os.chmod(path, stats.st_mode | 0o111)
