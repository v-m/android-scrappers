#!/usr/bin/env python

import datetime
import json
import os
import sys

import urllib3
import bs4
import urllib.parse as urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://apkpure.com/"
SEARCH_PACKAGE_URL = 'https://apkpure.com/dl/{}'


def find_package_page(package_name):
    http = urllib3.PoolManager()
    r = http.request("GET", SEARCH_PACKAGE_URL.format(package_name))
    return r.geturl()


def pull_page_info(app_href):
    try:
        soup = bs4_parse_url(build_app_page_url(app_href))

        title = soup.select_one("div.title-like > h1").text
        author = soup.select_one("div.details-author span").text
        icon = soup.select_one("dl.ny-dl div.icon img")['src']

        return title, author, icon
    except AttributeError:
        return None


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


def parse_versions(soup, only_last=False):
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

        if only_last:
            break

    return ret


def proceed_app(title, developer, icon, relative_href, latest=False):
    app = {
        "title": title,
        "developer": developer,
        "icon": icon,
        "href": build_app_page_url(relative_href),
        "nb_versions": -1,
        "versions": None
    }

    versions_soup = bs4_parse_url(build_app_download_page_url(relative_href))
    versions_soup = versions_soup.select("div.ver > ul > li > a")
    app['nb_versions'] = len(versions_soup)
    app['versions'] = parse_versions(versions_soup, latest)

    if len(app['versions']) == 0:
        print("No version found for: {}".format(app['href']), file=sys.stderr)
        return None

    return app


def persist_apps(file, apps):
    with open(file, "w") as fp:
        json.dump(apps, fp)


def load_apps(file):
    if os.path.exists(file):
        with open(file, "r") as fp:
            return json.load(fp)

    return None


def init(file, nb_apps, author):
    start_time = datetime.datetime.now()

    apps = {
        "_source": "APKPure",
        "_nb_apps": nb_apps,
        "_date": str(datetime.datetime.now()),
        "_author": author,
        "_elapsed": None,
        "apps": {}
    }

    persist_apps(file, apps)

    return apps, start_time
