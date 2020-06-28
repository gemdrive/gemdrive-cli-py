This is a simple python script for interacting with GemDrive servers. The
available commands are described below:


# ls

Prints a simple directory listing. Doesn't currently work for files.

```bash
./gemdrive_cli.py ls https://gemdrive.io
```

# sync

Recursively makes a local directory structure match the given GemDrive
directory.

To download to the current working directory:

```bash
./gemdrive_cli.py sync https://gemdrive.io/
```

Or specify a destination:

```bash
./gemdrive_cli.py sync https://gemdrive.io/ dest_dir
```

Be sure to include the trailing '/', otherwise it will download it as a file.

Speaking of which, sync also works for downloading single files:

```bash
./gemdrive_cli.py sync https://gemdrive.io/gemdrive_logo.png
```

That is similar to running:

```bash
wget https://gemdrive.io/gemdrive_logo.png
```

or

```bash
curl https://gemdrive.io/gemdrive_logo.png > gemdrive_logo.png
```


## sync limitations

* Currently uses only file size to determine if a file already exists locally.
  If you must be sure they match, delete the local files first.
* Currently not optimized. Trees with lots of directories and small files will
  sync much slower.
