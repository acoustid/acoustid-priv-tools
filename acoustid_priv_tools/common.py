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
import logging
import ConfigParser


class Config(object):

    def __init__(self, parser):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(os.path.expanduser('~/.config/acoustid-priv.conf'))
        self.parser = parser
        self.parser.add_argument('--api-key', help='AcoustID.biz API key')
        self.parser.add_argument('--catalog', help='Catalog name')
        self.parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    def parse_args(self):
        self.args = self.parser.parse_args()
        log_level = logging.INFO
        if self.args.verbose:
            log_level = logging.DEBUG
        logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
        return self.args

    def get_api_key(self):
        if self.args.api_key:
            return self.args.api_key
        if self.config.has_option('main', 'api-key'):
            return self.config.get('main', 'api-key')
        self.parser.error('missing api key')

    def get_catalog(self):
        if self.args.catalog:
            return self.args.catalog
        if self.config.has_option('main', 'catalog'):
            return self.config.get('main', 'catalog')
        self.parser.error('missing catalog')
