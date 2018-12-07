"""Download APKs from a JSON APKPure file"""
__author__ = "Vincenzo Musco (http://www.vmusco.com)"
__date__ = "2018-11-27"

import queue
import sqlite3
import threading
import argparse
import json
import os
import subprocess
import sys


class DownloadThread(threading.Thread):
    def __init__(self, thread_id, download_queue, working_folder, last, link):
        super().__init__()
        self.id = thread_id
        self.download_queue = download_queue
        self.working_folder = working_folder
        self.last = last
        self.alive = True
        self.db, self.apps = None, None

        if type(link) != dict:
            self.db = link
        else:
            self.apps = link

    def run(self):
        while self.alive:
            self.alive = download_job(self.download_queue, self.working_folder, self.last,
                                      self.db if self.db is not None else self.apps, self.id)


def download_job(download_queue, working_folder, last, src, identity=0):
    try:
        package_name = download_queue.get(False, 5)
        print(identity, package_name)

        if "." in package_name:
            package_folder = os.path.join(working_folder, "{}_app".format(package_name))

            if not os.path.exists(package_folder):
                os.makedirs(package_folder)

            if type(src) != dict:
                versions = []

                for row in src.execute("SELECT name, download_link FROM versions WHERE id = "
                                       "(SELECT id FROM apps WHERE package = ?) ORDER BY updated DESC;",
                                      (package_name,)):
                    versions.append({"name": row[0], "download_link": row[1]})
            else:
                versions = src['apps'][package_name]['versions']

            if len(versions) > 0:
                if last:
                    versions = [versions[0]]

                for version in versions:
                    version_folder = os.path.join(package_folder, version['name'])

                    if not os.path.exists(version_folder):
                        os.makedirs(version_folder)
                    elif len(os.listdir(version_folder)) > 0:
                        continue

                    subprocess.Popen(['curl', '-O', '-L', '-J', '-f', version['download_link']], cwd=version_folder)

        return True
    except queue.Empty:
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="Source File")
    parser.add_argument("working_folder", type=str, help="Where to download stuffs")
    parser.add_argument("--sqlite", action='store_true',
                        help="Source file is a sqlite3 database instead of a json file")
    parser.add_argument("--last", action='store_true', help="Download only last version")
    parser.add_argument("--threads", type=int, help="Split the work across several threads.", default=1)

    args = parser.parse_args()

    if not os.path.exists(args.working_folder):
        os.makedirs(args.working_folder)
    elif not os.path.isdir(args.working_folder):
        print("Working dir exists and is not a directory!")
        sys.exit(1)

    db = None

    if args.sqlite:
        db = sqlite3.connect(args.file, check_same_thread=False)
        apps = map(lambda x: x[0], db.execute("SELECT package FROM apps WHERE id IN (SELECT DISTINCT(id) FROM versions)").fetchall())
    else:
        with open(args.file) as fp:
            js = json.load(fp)
        apps = js['apps']

    download_queue = queue.Queue()
    for app in apps:
        download_queue.put_nowait(app)

    if args.threads > 1:
        for i in range(args.threads):
            print("Spawning thread {}".format(i))
            thread = DownloadThread(i, download_queue, args.working_folder, args.last, db if db is not None else js)
            thread.start()
    else:
        download_job(download_queue, args.working_folder, args.last, db if db is not None else js, 0)
