# -*- coding: utf-8 -*-
#
import re
import json
import requests
from bs4 import BeautifulSoup


URL_SERVER_FILMS = 'https://redecanais.cloud'
URL_SERVER_TV = 'https://redecanaistv.com/'


class ProxyRequests:
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


class Browser:

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
        with self.session as s:
            payload = data
            self.response = s.post(url=url, data=payload, proxies=proxies)
            if self.response.status_code == 200:
                print(proxies)
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
            return response.text

        return None


class Resolver(Browser):

    def __init__(self):
        super().__init__()
        self.is_tv = False
        self.stream_ref = None
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
        soup = BeautifulSoup(html, 'html.parser')
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
                dict_films = {'title': result.img['alt'], 'url': URL_SERVER_FILMS + result['href'], 'img': img, 'description': result_dict['desc'], 'player': result_dict['player'], 'stream': result_dict['stream']}
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
        soup = BeautifulSoup(html, 'html.parser')
        player, stream = self.get_player_id(soup)
        try:
            tags = soup.find('div', {'id': 'content-main'})
            films = tags.find_all('div', {'itemprop': 'description'})
            if not films:
                result = {'desc': 'Conteúdo sem descrição!!!', 'player': player, 'stream': stream, 'referer': self.stream_ref}
                return result
            else:
                for info in films:
                    result = {'desc': info.text.replace('\n', ''), 'player': player, 'stream': stream, 'referer': self.stream_ref}
                    return result
        except ValueError:
            result = {'desc': None, 'player': None, 'stream': None, 'referer': self.stream_ref}
            return result

    def get_player_id(self, iframe):
        try:
            url_player = iframe.find('div', {'id': 'video-wrapper'}).iframe['src']
            player, stream = self.get_player(url_player)
        except ValueError:
            player = None
            stream = None
        return player, stream

    def get_player(self, url):
        url_player = self.url_server + url
        self.response = self.send_request('GET', url_player, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            return url_player, self.decrypt_link(url_action, value)

    def decrypt_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            return self.redirect_link(url_action, value)

    def redirect_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            form = BeautifulSoup(self.response, 'html.parser').find('form')
            url_action = form['action']
            value = form.input['value']
            return self.get_ads_link(url_action, value)

    def get_ads_link(self, url, value):
        self.headers["referer"] = self.referer
        payload = {
            "data": value
        }
        self.response = self.send_request('POST', url, data=payload, headers=self.headers)
        if self.response:
            iframe = BeautifulSoup(self.response, 'html.parser').find('iframe')
            url_action = iframe['src']
            return self.get_stream(url + url_action.replace('./', '/'), url)

    def get_stream(self, url, referer):
        self.headers["referer"] = referer
        self.stream_ref = referer
        self.response = self.send_request('GET', url, headers=self.headers)
        if self.response:
            soup = BeautifulSoup(self.response, 'html.parser')
            if self.is_tv:
                return re.compile(r'source: "(.*?)",').findall(self.response)[0]
            download_url = self.get_url_download_video(soup.find('div', {'id': 'instructions'}).video['baixar'])
            if download_url:
                return download_url
            return soup.find('div', {'id': 'instructions'}).source['src'].replace('\n', '').split('?')[0]

    def get_url_download_video(self, url):
        self.response = self.send_request('GET', url, headers=self.headers)
        link_download = None
        if self.response:
            link_download = re.compile(r'<meta .*?0; URL=(.*?)"/>').findall(self.response)[0].replace("'", "")
        return link_download
