"""Download APKs from a JSON APKPure file"""

__author__ = "Vincenzo Musco (http://www.vmusco.com)"
__date__ = "2018-11-27"

import argparse
import json
import os
import subprocess
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("json", type=str, help="JSON File")
    parser.add_argument("working_folder", type=str, help="Where to download stuffs")
    parser.add_argument("--last", action='store_true', help="Download only last version")

    args = parser.parse_args()

    with open(args.json) as fp:
        js = json.load(fp)

    if not os.path.exists(args.working_folder):
        os.makedirs(args.working_folder)
    elif not os.path.isdir(args.working_folder):
        print("Working dir exists and is not a directory!")
        sys.exit(1)

    for package_name in js['apps']:
        print(package_name)

        if "." not in package_name:
            continue

        # package_name = app['href'].split("/")[-1]
        package_folder = os.path.join(args.working_folder, "{}_app".format(package_name))

        app = js['apps'][package_name]

        if not os.path.exists(package_folder):
            os.makedirs(package_folder)

        versions = app['versions']

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
