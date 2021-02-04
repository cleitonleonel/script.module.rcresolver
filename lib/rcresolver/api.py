# -*- coding: utf-8 -*-
#
from .resolver import Resolver


def resolve(url):
	result = Resolver()
	return result.find_streams(url)
