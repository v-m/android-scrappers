"""Download APKs from a JSON APKPure file"""
import sqlite3

__author__ = "Vincenzo Musco (http://www.vmusco.com)"
__date__ = "2018-11-27"

import argparse
import json
import os
import subprocess
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="Source File")
    parser.add_argument("working_folder", type=str, help="Where to download stuffs")
    parser.add_argument("--sqlite", action='store_true',
                        help="Source file is a sqlite3 database instead of a json file")
    parser.add_argument("--last", action='store_true', help="Download only last version")

    args = parser.parse_args()

    if not os.path.exists(args.working_folder):
        os.makedirs(args.working_folder)
    elif not os.path.isdir(args.working_folder):
        print("Working dir exists and is not a directory!")
        sys.exit(1)

    db = None

    if args.sqlite:
        db = sqlite3.connect(args.file)
        apps = map(lambda x: x[0], db.execute("SELECT package FROM apps WHERE EXISTS("
                                              "SELECT * FROM versions WHERE versions.id = apps.id)").fetchall())
    else:
        with open(args.file) as fp:
            js = json.load(fp)
        apps = js['apps']

    for package_name in apps:
        print(package_name)

        if "." not in package_name:
            continue

        package_folder = os.path.join(args.working_folder, "{}_app".format(package_name))

        if not os.path.exists(package_folder):
            os.makedirs(package_folder)

        if db:
            versions = []

            for row in db.execute("SELECT name, download_link FROM versions WHERE id = "
                                  "(SELECT id FROM apps WHERE package = ?) ORDER BY updated DESC;", (package_name,)):
                versions.append({"name": row[0], "download_link": row[1]})
        else:
            versions = js['apps'][package_name]['versions']

        if len(versions) < 1:
            continue

        if args.last:
            versions = [versions[0]]

        for version in versions:
            version_folder = os.path.join(package_folder, version['name'])

            if not os.path.exists(version_folder):
                os.makedirs(version_folder)
            elif len(os.listdir(version_folder)) > 0:
                continue

            subprocess.run(['curl', '-O', '-L', '-J', '-f', version['download_link']], cwd=version_folder)
