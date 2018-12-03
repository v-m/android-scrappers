"""Download apps package informations from Google Play Store"""

__author__ = "Vincenzo Musco (http://www.vmusco.com)"
__date__ = "2018-12-03"

import argparse
import csv
import json

from apkpure_to_json import bs4_parse_url

BASE_URL = "https://play.google.com/store/apps/details?id={}"


def google_store_metadata(package):
    print("Scrapping {}".format(package))
    _soup_element = bs4_parse_url(BASE_URL.format(package))

    found = {}
    for e in _soup_element.select("h2"):
        if "Additional Information" in e.text:
            par = e.parent.parent
            for link in par.select("a"):
                link.decompose()
            for entry in e.parent.parent.select("div")[2].find_all("div", recursive=False):
                if entry.select("div")[1].text != "" and entry.select("div")[0].text != entry.select("div")[1].text:
                    found[entry.select("div")[0].text] = entry.select("div")[1].text

    return found


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("out_file", type=str, help="The file to produce with results")
    parser.add_argument("package", type=str, nargs="*", help="The package to query")
    parser.add_argument("--csv", action='store_true', help="Store into a CSV file")

    args = parser.parse_args()

    result = {}

    for package in args.package:
        result[package] = google_store_metadata(package)

        keys = result[package].keys()

        with open(args.out_file, "w") as fp:
            if args.csv:
                writer = csv.writer(fp)

                writer.writerow(["Package"] + list(keys))
                for pkg in result:
                    writer.writerow([pkg] + [result[pkg][key] for key in keys])

            else:
                json.dump(result, fp)
