# -*- coding: utf-8 -*-
#
from .resolver import Resolver

result = Resolver()


def resolve(url):
	return result.find_streams(url)


def make_m3u(file_path):
	return result.generate_playlist_m3u(file_path)
