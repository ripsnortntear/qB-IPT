# VERSION: 1.01
# AUTHORS: txtsd (thexerothermicsclerodermoid@gmail.com)

# iptorrents.py - A plugin for qBittorrent to search on iptorrents.com
# Copyright (C) 2019  txtsd <thexerothermicsclerodermoid@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import gzip
import io
import logging
import re
import tempfile
import urllib.request as request
from http.cookiejar import CookieJar
from urllib.error import URLError
from urllib.parse import urlencode, quote

from helpers import htmlentitydecode
from novaprinter import prettyPrinter

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class iptorrents(object):
    # Login information ######################################################
    #
    # SET THESE VALUES!!
    #
    username = "your_username"
    password = "your_password"
    ###########################################################################
    url = 'https://iptorrents.com'
    name = 'IPTorrents'
    supported_categories = {
        'all': '',
        'movies': '72',
        'tv': '73',
        'music': '75',
        'games': '74',
        'anime': '60',
        'software': '1',
        'pictures': '36',
        'books': '35'
    }

    def __init__(self):
        """
        Class initialization
        Requires personal login information
        """
        self.ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0'
        self.session = None

        self._login()

    def _login(self):
        """Initiate a session and log into IPTorrents"""
        # Build opener
        cj = CookieJar()
        params = {
            'username': self.username,
            'password': self.password
        }
        session = request.build_opener(request.HTTPCookieProcessor(cj))

        # change user-agent
        session.addheaders.pop()
        session.addheaders.append(('User-Agent', self.ua))
        session.addheaders.append(('Referrer', self.url + '/login.php'))

        # send request
        try:
            logging.debug("Trying to connect using given credentials.")
            logging.debug(self.url + '/take_login.php')
            logging.debug(urlencode(params).encode('utf-8'))
            session.open(
                self.url + '/take_login.php',
                urlencode(params).encode('utf-8')
            )
            logging.debug("Connected using given credentials.")
            self.session = session
        except URLError as errno:
            print("Connection Error: {} {}".format(errno.code, errno.reason))
            return

    def _get_link(self, link):
        """Return the HTML content of url page as a string """
        try:
            logging.debug("Trying to open " + link)
            res = self.session.open(link)
        except URLError as errno:
            print("Connection Error: {} {}".format(errno.code, errno.reason))
            return ""

        charset = 'utf-8'
        info = res.info()
        _, charset = info['Content-Type'].split('charset=')
        data = res.read()
        data = data.decode(charset, 'replace')

        data = htmlentitydecode(data)
        return data

    def search_parse(self, link, page=1):
        """ Parses IPTorrents for search results and prints them"""
        logging.debug("Parsing " + link)
        data = self._get_link(link + '&p=' + str(page))
        _tor_table = re.search('<form>(<table id=torrents.+?)</form>', data)
        tor_table = _tor_table.groups()[0] if _tor_table else None

        results = re.finditer(
            r'<a class=" hv" href="(?P<desc_link>/details.+?)">(?P<name>.+?)</a>.+?href="(?P<link>/download.+?)".+?(?P<size>\d+?\.*?\d*? (|K|M|G)B)<.+?t_seeders">(?P<seeds>\d+).+?t_leechers">(?P<leech>\d+?)
