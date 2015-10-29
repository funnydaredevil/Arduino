#!/usr/bin/env python
# This script will download and extract required tools into the current directory
# Tools list is obtained from tools.json file
# Written by Ivan Grokhotkov, 2015
#
from __future__ import print_function
import urllib
import os
import os.path
import hashlib
import json
import platform
import sys
import tarfile
import zipfile
import re

dist_dir = 'dist/'

def sha256sum(filename, blocksize=65536):
    hash = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()

def report_progress(count, blockSize, totalSize):
    percent = int(count*blockSize*100/totalSize)
    percent = min(100, percent)
    sys.stdout.write("\r%d%%" % percent)
    sys.stdout.flush()

def unpack(filename, destination):
    dirname = ''
    print('Extracting {0}'.format(filename))
    if filename.endswith('tar.gz'):
        tfile = tarfile.open(filename, 'r:gz')
        tfile.extractall(destination)
        dirname= tfile.getnames()[0]
    elif filename.endswith('zip'):
        zfile = zipfile.ZipFile(filename)
        zfile.extractall(destination)
        dirname = zfile.namelist()[0]
    else:
        raise NotImplementedError('Unsupported archive type')

    # a little trick to rename tool directories so they don't contain version number
    rename_to = re.match(r'^([a-z][^\-]*\-*)+', dirname).group(0).encode('ascii').strip('-')
    if rename_to != dirname:
        print('Renaming {0} to {1}'.format(dirname, rename_to))
        os.rename(dirname, rename_to)

def get_tool(tool):
    archive_name = tool['archiveFileName']
    local_path = dist_dir + archive_name
    url = tool['url']
    real_hash = tool['checksum'].split(':')[1]
    if not os.path.isfile(local_path):
        print('Downloading ' + archive_name);
        urllib.urlretrieve(url, local_path, report_progress)
        sys.stdout.write("\rDone\n")
        sys.stdout.flush()
    else:
        print('Tool {0} already downloaded'.format(archive_name))
    local_hash = sha256sum(local_path)
    if local_hash != real_hash:
        print('Hash mismatch for {0}, delete the file and try again'.format(local_path))
        raise RuntimeError()
    unpack(local_path, '.')

def load_tools_list(filename, platform):
    tools_info = json.load(open(filename))
    tools_to_download = []
    for t in tools_info:
        tool_platform = [p for p in t['systems'] if p['host'] == platform]
        if len(tool_platform) == 0:
            continue
        tools_to_download.append(tool_platform[0])
    return tools_to_download

def identify_platform():
    arduino_platform_names = {'Darwin'  : {32 : 'i386-apple-darwin', 64 : 'x86_64-apple-darwin'},
                              'Linux'   : {32 : 'i686-pc-linux-gnu', 64 : 'x86_64-pc-linux-gnu'},
                              'Windows' : {32 : 'i686-mingw32',      64 : 'i686-mingw32'}}
    bits = 32
    if sys.maxsize > 2**32:
        bits = 64
    return arduino_platform_names[platform.system()][bits]

if __name__ == '__main__':
    print('Platform: {0}'.format(identify_platform()))
    tools_to_download = load_tools_list('tools.json', identify_platform())
    for tool in tools_to_download:
        get_tool(tool)
