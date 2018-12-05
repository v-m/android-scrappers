"""Download app informations (and download link) from APKPure for a specific list of app packages"""
import datetime
import os

__author__ = "Vincenzo Musco (http://www.vmusco.com)"
__date__ = "2018-11-27"

import argparse
import urllib3
import sqlite3

from apkpure_to_json import proceed_app, find_package_page, pull_page_info

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", action='store_true', help="Consider only the latest version of apps")
    parser.add_argument("--author", type=str, help="The scrapper author string", default="Anonymous")

    parser.add_argument("file", type=str, help="The produced file")
    parser.add_argument("packages", nargs='*', type=str, help="The search keyword")

    args = parser.parse_args()
    considered_apps = args.packages

    start_time_script = datetime.datetime.now()

    build_tables = not os.path.exists(args.file)
    db = sqlite3.connect(args.file)

    if build_tables:
        db.execute("""CREATE TABLE apps (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                          package TEXT NOT NULL UNIQUE,
                                          title TEXT,
                                          developer TEXT,
                                          icon TEXT,
                                          href TEXT,
                                          nb_versions INTEGER DEFAULT -1);""")

        db.execute("""CREATE TABLE versions (id, 
                                             name TEXT,
                                             href TEXT,
                                             size TEXT,
                                             type TEXT,
                                             source TEXT,
                                             updated TEXT,
                                             package TEXT,
                                             version_vid TEXT,
                                             lang TEXT,
                                             download_link TEXT);""")

        db.execute("""CREATE INDEX versions_index ON versions(id);""")
        db.execute("""CREATE INDEX apps_package ON apps(package);""")

        db.commit()

    if considered_apps is not None:
        for app in considered_apps:
            try:
                db.execute("INSERT INTO apps (package) VALUES (?);", (app,))
            except sqlite3.IntegrityError:
                # app already queued
                pass

    db.commit()

    query = "SELECT package " \
            "FROM apps " \
            "WHERE NOT EXISTS (SELECT * FROM versions WHERE versions.id = apps.id)" \
            "ORDER BY package"

    considered_apps = list(map(lambda x: x[0], db.execute(query).fetchall()))

    # print(considered_apps)

    for index, package in enumerate(considered_apps):
        print("[{}/{}] Scrapping {}".format(index + 1, len(considered_apps), package), end='', flush=True)

        app_href = find_package_page(package)
        app_infos = pull_page_info(app_href)

        if app_infos is None:
            print("...Not found")
            continue

        try:
            app = proceed_app(*app_infos, app_href, args.latest)

            db.execute("""UPDATE apps 
                          SET title = ?, developer = ?, icon = ?, href = ?, nb_versions = ? 
                          WHERE id = (SELECT id FROM apps WHERE package = ?)""", (app['title'], app['developer'],
                                                                                  app['icon'], app['href'],
                                                                                  app['nb_versions'], package))

            for v in app['versions']:
                params = (package, v['name'], v['href'], v['size'], v['type'], v['source'], v['update'], v['package'],
                          v['version_vid'], v['lang'], v['download_link'])

                db.execute("""INSERT INTO versions (id, name, href, size, type, source, updated, package, version_vid, 
                              lang, download_link) 
                              VALUES ((SELECT id FROM apps WHERE package = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                           params)


            print("...{} versions".format(len(app['versions'])))
            db.commit()
        except TypeError as e:
            print(e)
            print("...Error")
            pass