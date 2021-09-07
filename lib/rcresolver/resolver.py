# -*- coding: utf-8 -*-
#
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import parse_qsl, unquote, urlparse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

URL_SERVER_FILMS = 'https://redecanais.re'
URL_SERVER_TV = 'https://redecanaistv.net/'


def app(environ, start_response):
    browser = Browser()
    result = None
    if environ['REQUEST_METHOD'] == 'GET':
        query = environ["QUERY_STRING"]
        if 'url' not in query:
            headers = [('Content-Type', 'text/plain')]
            start_response('404 Not Found!', headers)
            return ['Página não encontrada!'.encode()]
        url = dict(parse_qsl(query))['url']
        with requests.Session() as session:
            retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
            if 'https://' in url:
                session.mount('https://', HTTPAdapter(max_retries=retries))
            else:
                session.mount('http://', HTTPAdapter(max_retries=retries))
            response = session.get(url, headers=browser.headers(), timeout=0.5)
        if response:
            result = response.content[8:]
        headers = [('Content-Type', 'video/mp2t'),
                   ('User-Agent', browser.headers()['User-Agent'])]
        start_response('200 OK', headers)
        return [result]


class LocalHttpProxy(object):

    def __init__(self):
        self.host = None
        self.port = None
        self.server_class = WSGIServer
        self.handler_class = WSGIRequestHandler

    def set_config(self, host, port):
        self.host = host
        self.port = port

    def runserver(self):
        http_server = self.server_class((self.host, self.port), self.handler_class)
        http_server.set_app(app)
        if http_server:
            print(f"Serving on port http://{self.host}:{self.port} ...")
        return http_server.serve_forever()


class ProxyRequests(object):

    def __init__(self):
        self.sockets = []
        self.acquire_sockets()
        self.proxies = self.mount_proxies()

    def acquire_sockets(self):
        response = requests.get(
            'https://api.proxyscrape.com/?request=displayproxies&proxytype='
            'http&timeout=7000&country=BR&anonymity=elite&ssl=yes'
        ).text
        self.sockets = response.split('\n')

    def mount_proxies(self):
        current_socket = self.sockets.pop(0)
        proxies = {
            'http': self.sockets,
        }
        return proxies


class Browser(object):

    def __init__(self):
        self.request = None
        self.response = None
        self.proxies = None
        self.referer = None
        self.url_server = None
        self.session = requests.Session()

    def headers(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
        }
        return headers

    def verify_proxy(self, url, proxies, data):
        with self.session as session:
            payload = data
            self.response = session.post(url=url, data=payload, proxies=proxies)
            if self.response.status_code == 200:
                self.proxies = proxies
                return True

    def set_proxies(self, **kwargs):
        if kwargs:
            self.proxies = kwargs
            return self.proxies
        else:
            self.proxies = ProxyRequests().proxies

    def send_request(self, method, url, **kwargs):
        if self.proxies:
            if type(self.proxies['http']) == list:
                for proxy in self.proxies['http']:
                    proxies = {
                        'http': 'http://' + proxy.replace('\r', ''),
                    }
                    result = self.verify_proxy(url, proxies, data=kwargs)
                    if result:
                        break

        response = self.session.request(method, url, proxies=self.proxies, **kwargs)
        if response.status_code == 200:
            self.referer = url
            return response
        return None


class Resolver(Browser):

    def __init__(self):
        super().__init__()
        self.is_tv = False
        self.stream_ref = None
        self.player_url = None
        self.base_player = None
        self.download_url = None
        self.link_download = None
        self.source_url = None
        self.headers = self.headers()

    def create_json(self, data, filename=None):
        if filename:
            path = filename
        else:
            path = 'filmes.json'
        dumps = json.dumps(data, indent=4, sort_keys=True)
        with open(path, 'w') as file:
            file.write(dumps)

    def films(self, url):
        html = self.send_request('GET', url)
        soup = BeautifulSoup(html.text, 'html.parser')
        tags = soup.find('ul', {'class': 'row pm-ul-browse-videos list-unstyled'})
        films_list = []
        try:
            films = tags.find_all('div', {'class': 'pm-video-thumb'})
            for info in films:
                result = info.find_all('a')[1]
                if 'https' not in result.img['data-echo']:
                    img = URL_SERVER_FILMS + result.img['data-echo']
                else:
                    img = result.img['data-echo']
                result_dict = self.find_streams(URL_SERVER_FILMS + result['href'])
                dict_films = {
                    'title': result.img['alt'],
                    'url': URL_SERVER_FILMS + result['href'],
                    'img': img,
                    'description': result_dict['description'],
                    'download_link': self.link_download,
                    'player': result_dict['player'],
                    'stream': result_dict['stream'],
                    'referer': self.stream_ref
                }
                films_list.append(dict_films)
            return films_list
        except ValueError:
            dict_films = {}
            return films_list.append(dict_films)

    def find_streams(self, url):
        self.url_server = URL_SERVER_FILMS
        if 'tv' in url:
            self.is_tv = True
            self.url_server = URL_SERVER_TV
        self.headers['referer'] = self.url_server
        html = self.send_request('GET', url, headers=self.headers)
        soup = BeautifulSoup(html.text, 'html.parser')
        self.get_player_id(soup)
        try:
            tags = soup.find('div', {'id': 'content-main'})
            films = tags.find_all('div', {'itemprop': 'description'})
            if not films:
                result = {
                    'description': 'Conteúdo sem descrição!!!',
                    'player': self.player_url,
                    'download_link': self.link_download,
                    'download': self.download_url,
                    'source': self.source_url,
                    'referer': self.stream_ref
                }
                return result
            else:
                for info in films:
                    result = {
                        'description': info.text.replace('\n', ''),
                        'player': self.player_url,
                        'download_link': self.link_download,
                        'download': self.download_url,
                        'source': self.source_url,
                        'referer': self.stream_ref
                    }
                    return result
        except ValueError:
            result = {
                'description': None,
                'player': self.player_url,
                'download_link': self.link_download,
                'download': self.download_url,
                'source': self.source_url,
                'referer': self.stream_ref
            }
            return result

    def get_player_id(self, iframe):
        try:
            url_player_before = iframe.find('div', {'id': 'video-wrapper'}).iframe['src']
            self.player_url = self.url_server + url_player_before
            self.get_player()
        except ValueError:
            return None

    def get_player(self):
        self.response = self.send_request('GET', self.player_url, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response.text, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            self.base_player = value.replace('&=', '')
            self.decrypt_link(url_action, value)

    def decrypt_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response.text, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            self.redirect_link(url_action, value)

    def redirect_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response.text, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            self.get_ads_link(url_action, value)

    def get_ads_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            iframe = BeautifulSoup(self.response.text, 'html.parser').find('iframe')
            url_action = iframe['src']
            self.get_stream(url + url_action.replace('./', '/'), url)

    def get_stream(self, url, referer):
        self.headers["referer"] = referer
        self.stream_ref = referer + self.base_player
        self.response = self.send_request('GET', url, headers=self.headers)
        if self.response:
            soup = BeautifulSoup(self.response.text, 'html.parser')
            if self.is_tv:
                self.source_url = soup.source['src']
                return self.source_url
                # return re.compile(r'source: "(.*?)",').findall(self.response)[0]
            try:
                source = soup.find('div', {'id': 'instructions'}).source['src'].replace('\n', '').replace('./', '/')
                self.source_url = f"{'/'.join(self.referer.split('/')[:-5])}{source}"
                self.download_url = soup.find('div', {'id': 'instructions'}).video['baixar']
                if self.download_url:
                    self.get_url_download_video()
            except:
                self.source_url = None
                self.download_url = None

    def get_url_download_video(self):
        try:
            self.response = self.send_request('GET', self.download_url, headers=self.headers)
            if self.response:
                self.link_download = re.compile(r'<meta .*?0; URL=(.*?)"/>').findall(self.response.text)[0].replace("'",
                                                                                                                    "")
            return self.link_download
        except:
            self.link_download = None

    def generate_playlist_m3u(self, path_m3u):
        response = self.send_request('GET', self.source_url, headers=self.headers)
        file_path = None
        if response:
            url = response.text.replace('https://', 'http://127.0.0.1:3333/?url=https://').replace('.png', '.png&')
            file_path = path_m3u.replace('\\', '/') + 'redecanais_vip_playlist.m3u8'
            with open(file_path, "w", encoding="utf-8") as file_m3u:
                file_m3u.write(url)
        return file_path
