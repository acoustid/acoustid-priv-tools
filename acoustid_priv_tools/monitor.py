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

import sys
import time
import threading
import logging
import pprint
import csv
import argparse
import datetime
import urllib
import requests
import subprocess
import Queue
import json
from contextlib import contextmanager
from acoustid_priv_tools.common import Config

logger = logging.getLogger(__name__)


@contextmanager
def create_ffmpeg_process(url):
    ffmpeg_command = ['ffmpeg', '-loglevel', 'fatal', '-i', url, '-f', 'wav', '-']
    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    ffmpeg_process.stdin.close()

    yield ffmpeg_process

    if ffmpeg_process.poll() is None:
        ffmpeg_process.kill()

    if ffmpeg_process.returncode != 0:
        logger.error('FFmpeg process exited with return code %s', ffmpeg_process.returncode)


@contextmanager
def create_fpcalc_process(ffmpeg_process, chunk_length):
    fpcalc_command = ['stdbuf', '-oL', 'fpcalc', '-json', '-ts', '-length', '0', '-chunk', str(chunk_length), '-overlap', '-']
    fpcalc_process = subprocess.Popen(fpcalc_command, stdin=ffmpeg_process.stdout, stdout=subprocess.PIPE, close_fds=True)
    ffmpeg_process.stdout.close()

    yield fpcalc_process

    if fpcalc_process.poll() is None:
        fpcalc_process.kill()

    if fpcalc_process.returncode != 0:
        logger.error('Audio fingerprint process exited with return code %s', fpcalc_process.returncode)


def read_process_stdout(process, queue):
    try:
        while True:
            line = process.stdout.readline()
            if line == '':
                break
            queue.put((True, json.loads(line.rstrip('\n'))))
    except Exception as ex:
        queue.put((False, ex))
    finally:
        queue.put((False, None))


def monitor_stream(url, chunk_length):
    with create_ffmpeg_process(url) as ffmpeg_process:
        with create_fpcalc_process(ffmpeg_process, chunk_length) as fpcalc_process:
            logger.debug('Monitoring %s', url)

            queue = Queue.Queue()

            thread = threading.Thread(target=read_process_stdout, args=(fpcalc_process, queue))
            thread.daemon = True
            thread.start()

            while True:
                result = queue.get()
                if result[0]:
                    yield result[1]
                else:
                    if result[1] is not None:
                        raise result[1]
                    else:
                        break


def main():
    parser = argparse.ArgumentParser(description='Monitor an audio stream.')
    parser.add_argument('url', help='URL of the audio stream')
    parser.add_argument('-o', '--output', help='Output CSV file')
    parser.add_argument('--chunk', type=int, default=30, help='Chunk duration')

    config = Config(parser)
    args = config.parse_args()

    api_key = config.get_api_key()
    catalog = config.get_catalog()

    session = requests.Session()
    session.auth = ('x-acoustid-api-key', api_key)

    base_url = 'https://api.acoustid.biz/v1/priv/{}'.format(urllib.quote(catalog, safe=''))
    rv = session.get(base_url)
    if rv.status_code == 404:
        logger.error('catalog does not exist')
        raise SystemExit(1)

    fieldnames = ['time', 'track_id', 'title', 'artist']

    def open_output_file(output, output_name, ts):
        if args.output:
            name = ts.strftime(args.output)
            if output is None or output_name != name:
                output = csv.DictWriter(open(name, 'a'), fieldnames=fieldnames)
        else:
            name = None
            if output is None:
                output = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        return output, name

    output = None
    output_name = None
    for chunk in monitor_stream(args.url, args.chunk):
        url = '{}/{}'.format(base_url, '_search')
        rv = session.post(url, json={'fingerprint': chunk['fingerprint'], 'stream': True})
        if rv.status_code != 200:
            logger.error('Search request failed')
            continue
        data = rv.json()
        ts = datetime.datetime.fromtimestamp(chunk['timestamp'])
        output, output_name = open_output_file(output, output_name, ts)
        for track in data['results']:
            logger.info('Found track %s (%s - %s)', track['id'], track['metadata'].get('artist'), track['metadata'].get('title'))
            output.writerow({
                'time': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'track_id': track['id'],
                'artist': track['metadata'].get('artist', '').encode('utf8'),
                'title': track['metadata'].get('title', '').encode('utf8'),
            })
            break
        else:
            logger.debug('No results')
            output.writerow({'time': ts.strftime('%Y-%m-%d %H:%M:%S'), 'track_id': '', 'artist': '', 'title': ''})


if __name__ == '__main__':
    main()
