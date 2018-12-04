"""Download APKs from APKPure for a specific keyword serarch term"""

__author__ = "Vincenzo Musco (http://www.vmusco.com)"
__date__ = "2018-11-27"

import argparse
import datetime
import sys

from apkpure_to_json import init, bs4_parse_url, persist_apps, proceed_app

BASE_URL = "http://apkpure.com/search-page?q={search_terms}&region={region}&begin={page}"
PER_PAGE = 10


def build_search_url(search_criteria, region="US", page=0, increment=10):
    return BASE_URL.format(search_terms=search_criteria.replace(" ", "+"), region=region, page=page * increment)


def progress_det(nb):
    print("{}...".format(nb), end="", flush=True)


def find_nb_entries(keyword, region="US", progress_fct=None):
    _page = 0
    _apps = set()

    while True:
        _soup_element = bs4_parse_url(build_search_url(keyword, region, _page, PER_PAGE))

        if _soup_element.body.text.strip() == "":
            break

        for _app_entry in _soup_element.select("dl.search-dl"):
            _dt_element = _app_entry.select("dt")[0]
            title = _dt_element.select("a")[0]['title']
            _apps.add(title)

        if progress_fct:
            progress_fct(len(_apps))
        _page += 1

    return len(_apps), _page - 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("terms", type=str, help="The search keyword")
    parser.add_argument("file", type=str, help="The produced file")
    parser.add_argument("--latest", action='store_true', help="Consider only the latest version of apps")
    parser.add_argument("--author", type=str, help="The scrapper author string", default="Anonymous")
    parser.add_argument("--region", type=str, default="US", help="The country code region")

    args = parser.parse_args()

    page = 0

    print("Determining # entries...", end=" ", file=sys.stderr, flush=True)
    nb_apps, nb_pages = find_nb_entries(args.terms, args.region, progress_det)

    apps, start_time = init(args.file, nb_apps, args.author)
    apps_set = set()
    apps["_search_term"] = args.terms

    print("\nDone. Total apps: {}".format(nb_apps))

    for page in range(nb_pages):
        print("Processing page {page} of {total_pages}:".format(page=page, total_pages=nb_pages), end=" ", flush=True)
        soup = bs4_parse_url(build_search_url(args.terms, args.region, page, PER_PAGE))

        for app_entry in soup.select("dl.search-dl"):
            dt_element = app_entry.select("dt")[0]
            app_title = dt_element.select("a")[0]['title']

            print("X" if app_title not in apps_set else "-", end="", flush=True)

            if app_title in apps_set:
                continue

            dd_element = app_entry.select("dd")[0]
            app_href = dt_element.select("a")[0]['href']

            app = proceed_app(app_title, dd_element.select("p > a")[1].text, dt_element.select("a > img")[0]['src'],
                              app_href, args.latest)

            if app is not None:
                apps['apps'][app['href'].split("/")[-1]] = app
                apps_set.add(app_title)

            apps['_elapsed'] = str(datetime.datetime.now() - start_time)
            persist_apps(args.file, apps)

        print("")
        page += 1