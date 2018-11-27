#!/usr/bin/env python

import datetime
import json
import argparse
import sys

import urllib3
import bs4
import urllib.parse as urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://apkpure.com/search-page?q={search_terms}&region={region}&begin={page}"


def build_url(search_criteria, region="US", page=0):
    return BASE_URL.format(search_terms=search_criteria.replace(" ", "+"), region=region, page=page * 15)


def build_app_page_url(rel_link):
    return urlparse.urljoin(BASE_URL, rel_link)


def build_app_download_page_url(rel_link):
    return "{}/versions".format(build_app_page_url(rel_link))


def bs4_parse_url(url):
    http = urllib3.PoolManager()
    r = http.request("GET", url)
    return bs4.BeautifulSoup(r.data, "html5lib")


def find_download_link(href):
    soup_element = bs4_parse_url(href)
    return soup_element.select_one("#download_link")['href']


def parse_versions(soup):
    ret = []

    for soup_version in soup:
        href = build_app_page_url(soup_version['href'])

        details = soup_version.select_one("div.ver-item")

        version_metadata = details.select_one("i.ver-item-m")
        version = {
            "name": details.select_one("span.ver-item-n").text,
            "href": href,
            "size": details.select_one("span.ver-item-s").text,
            "type": details.select_one("span.ver-item-t").text,
            "source": details.select("div.ver-item-a > p")[0].text,
            "update": details.select_one("div.ver-item-a > p.update-on").text,
            "package": version_metadata['data-p'],
            "version_vid": version_metadata['data-vid'],
            "lang": version_metadata['data-lang'],
            "download_link": find_download_link(href)
        }
        ret.append(version)

    return ret


def find_nb_entries(keyword, region="US", progress_fct=None):
    page = 0
    total = 0

    while True:
        soup_element = bs4_parse_url(build_url(keyword, region, page))

        if soup_element.body.text.strip() == "":
            break

        nb_in_page = len(soup_element.select("dl.search-dl"))
        total += nb_in_page

        # if nb_in_page < 14:
        #     break
        # else:
        if progress_fct:
            progress_fct(total)
        page += 1

    return total, page - 1


def persist_apps(file, apps):
    with open(file, "w") as fp:
        json.dump(apps, fp)


def progress_det(nb):
    print("{}...".format(nb), end="", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("terms", type=str, help="The search keyword")
    parser.add_argument("file", type=str, help="The produced file")
    parser.add_argument("--author", type=str, help="The scrapper author string", default="Anonymous")
    parser.add_argument("--region", type=str, default="US", help="The country code region")

    args = parser.parse_args()

    page = 0

    start_time = datetime.datetime.now()

    apps = {
        "_source": "APKPure",
        "_search_term": args.terms,
        "_nb_apps": None,
        "_nb_pages": None,
        "_date": str(datetime.datetime.now()),
        "_author": args.author,
        "_elapsed": None,
        "apps": []
    }

    persist_apps(args.file, apps)

    print("Determining # entries...", end=" ", file=sys.stderr, flush=True)

    nb_apps, nb_pages = find_nb_entries(args.terms, args.region, progress_det)
    apps["_nb_pages"] = nb_pages
    apps["_nb_apps"] = nb_apps

    print("\nDone. Total pages: {}".format(apps['_nb_pages']))

    persist_apps(args.file, apps)

    for page in range(nb_pages):
        print("Processing page {page} of {total_pages}:".format(page=page, total_pages=nb_pages), end=" ", flush=True)
        soup = bs4_parse_url(build_url(args.terms, args.region, page))

        for app_entry in soup.select("dl.search-dl"):
            print("X", end="", flush=True)

            dt_element = app_entry.select("dt")[0]
            dd_element = app_entry.select("dd")[0]

            app_href = dt_element.select("a")[0]['href']

            app = {
                "title": dt_element.select("a")[0]['title'],
                "developer": dd_element.select("p > a")[1].text,
                "icon": dt_element.select("a > img")[0]['src'],
                "href": build_app_page_url(app_href),
                "versions": None
            }

            versions_soup = bs4_parse_url(build_app_download_page_url(app_href))
            app['versions'] = parse_versions(versions_soup.select("div.ver > ul > li > a"))
            apps['apps'].append(app)
            apps['_elapsed'] = str(datetime.datetime.now() - start_time)
            persist_apps(args.file, apps)

        print("")
        page += 1
