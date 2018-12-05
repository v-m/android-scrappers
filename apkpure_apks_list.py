"""Download app informations (and download link) from APKPure for a specific list of app packages"""
import datetime
import os

__author__ = "Vincenzo Musco (http://www.vmusco.com)"
__date__ = "2018-11-27"

import argparse
import urllib3

from apkpure_to_json import init, persist_apps, proceed_app, find_package_page, pull_page_info, load_apps

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", action='store_true', help="Consider only the latest version of apps")
    parser.add_argument("--author", type=str, help="The scrapper author string", default="Anonymous")

    parser.add_argument("file", type=str, help="The produced file")
    parser.add_argument("packages", nargs='*', type=str, help="The search keyword")

    args = parser.parse_args()
    considered_apps = args.packages

    apps = load_apps(args.file)

    start_time_script = datetime.datetime.now()

    if apps is None:
        apps, start_time = init(args.file, len(considered_apps), args.author)
        apps["_packages"] = list(set(considered_apps))
    else:
        all_apps = set(considered_apps).union(apps["_packages"])
        apps["_packages"] = list(all_apps)

    persist_apps(args.file, apps)

    considered_apps = apps["_packages"]

    for index, package in enumerate(sorted(considered_apps)):
        print("[{}/{}] Scrapping {}".format(index + 1, len(considered_apps), package), end='')

        if package in apps['apps']:
            print("...Skipped")
            continue

        app_href = find_package_page(package)
        app_infos = pull_page_info(app_href)

        if app_infos is None:
            print("...Not found")
            continue

        try:
            app = proceed_app(*app_infos, app_href, args.latest)
        except:
            apps = None

        if app is not None:
            apps['apps'][package] = app
            print("...{} versions".format(len(app['versions'])))
        else:
            print("...Error")

        persist_apps(args.file, apps, start_time_script)
