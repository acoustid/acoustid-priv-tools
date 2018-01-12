# Copyright 2018, Lukas Lalinsky.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

import os
import base64
import hashlib
import logging
import argparse
import mediafile
import requests
import urllib
import ConfigParser
from acoustid_priv_tools.fpcalc import fingerprint_file_fpcalc

logger = logging.getLogger(__name__)


def sha1_file(path, maxlength=0):
    h = hashlib.sha256()
    with open(path, 'rb', buffering=0) as f:
        while True:
            b = f.read(128 * 1024)
            if not b:
                break
            h.update(b)
    return base64.urlsafe_b64encode(h.digest()).rstrip('=')


def main():
    config = ConfigParser.SafeConfigParser()
    config.read(os.path.expanduser('~/.config/acoustid-priv.conf'))

    try:
        default_api_key = config.get('main', 'api-key')
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        default_api_key = None

    try:
        default_catalog = config.get('main', 'catalog')
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        default_catalog = None

    parser = argparse.ArgumentParser(description='Synchronize your music collection.')
    parser.add_argument('--api-key', default=default_api_key, help='API key from acoustid.biz')
    parser.add_argument('--catalog', default=default_catalog, help='Catalog name')
    parser.add_argument('-d', '--directory', metavar='DIR',
                        help='directory with music files', required=True)
    parser.add_argument('--delete', action='store_true', help='Delete tracks on found in the directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    if not args.api_key:
        parser.error('missing API key')

    if not args.catalog:
        parser.error('missing catalog name')

    session = requests.Session()
    session.auth = ('x-acoustid-api-key', args.api_key)

    count_total = 0
    existing_tracks = {}

    base_url = 'https://api.acoustid.biz/v1/priv/{}'.format(urllib.quote(args.catalog, safe=''))
    rv = session.get(base_url, params={'tracks': '1'})
    if rv.status_code == 404:
        rv = session.put(base_url, json={})
    else:
        rv.raise_for_status()
        data = rv.json()
        while True:
            for track in data['tracks']:
                existing_tracks[track['id']] = track['metadata']
                count_total += 1
            if not data['has_more']:
                break
            rv = session.get(base_url, params={'tracks': '1', 'cursor': data['cursor']})
            rv.raise_for_status()
            data = rv.json()

    tracks = {}
    for root, dirnames, filenames in os.walk(args.directory):
        logger.debug('Scanning "%s"', root)
        for filename in filenames:
            path = os.path.join(root, filename)
            track_id = sha1_file(path)
            track = existing_tracks.get(track_id)
            if track is not None:
                logger.debug('Audio file "%s" already exists in the catalog as track %s', path, track_id)
            else:
                try:
                    mf = mediafile.MediaFile(path)
                except mediafile.FileTypeError:
                    continue
                logger.debug('Found audio file "%s"', path)
                track = {
                    'metadata': {
                        'title': mf.title,
                        'artist': mf.artist,
                    }
                }
            track['path'] = path
            tracks[track_id] = track

    count_added = 0
    tracks_to_add = set(tracks.keys()) - set(existing_tracks.keys())
    for track_id in tracks_to_add:
        info = tracks[track_id]
        _, fingerprint = fingerprint_file_fpcalc(info['path'], 0)
        metadata = dict(info['metadata'])
        logger.info('Adding track %s from "%s"', track_id, info['path'])
        url = '{}/{}'.format(base_url, urllib.quote(track_id, safe=''))
        rv = session.put(url, json={'fingerprint': fingerprint, 'metadata': metadata})
        rv.raise_for_status()
        count_added += 1
        count_total += 1

    count_deleted = 0
    if args.delete:
        tracks_to_delete = set(existing_tracks.keys()) - set(tracks.keys())
        for track_id in tracks_to_delete:
            logger.info('Deleting track %s', track_id)
            url = '{}/{}'.format(base_url, urllib.quote(track_id, safe=''))
            rv = session.delete(url, json={})
            rv.raise_for_status()
            count_deleted += 1
            count_total -= 1

    logger.info('%s tracks in the catalog, %s added, %s deleted', count_total, count_added, count_deleted)


if __name__ == '__main__':
    main()
