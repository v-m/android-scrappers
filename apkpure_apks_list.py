"""Download app informations (and download link) from APKPure for a specific list of app packages"""

__author__ = "Vincenzo Musco (http://www.vmusco.com)"
__date__ = "2018-11-27"

import argparse
import datetime

import urllib3

from apkpure_to_json import init, persist_apps, proceed_app, find_package_page, pull_page_info

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("packages", type=str, help="The search keyword")
    parser.add_argument("file", type=str, help="The produced file")
    parser.add_argument("--latest", action='store_true', help="Consider only the latest version of apps")
    parser.add_argument("--author", type=str, help="The scrapper author string", default="Anonymous")

    args = parser.parse_args()
    considered_apps = args.packages.split(",")

    apps, start_time = init(args.file, len(considered_apps), args.author)
    apps["_packages"] = considered_apps

    for index, package in enumerate(considered_apps):
        print("[{}/{}] Scrapping {}".format(index + 1, len(considered_apps), package))

        app_href = find_package_page(package)
        app_infos = pull_page_info(app_href)

        if app_infos is None:
            continue

        app = proceed_app(*app_infos, app_href, args.latest)

        if app is not None:
            apps['apps'].append(app)

        apps['_elapsed'] = str(datetime.datetime.now() - start_time)
        persist_apps(args.file, apps)