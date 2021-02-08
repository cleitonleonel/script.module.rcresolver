# -*- coding: utf-8 -*-
#
from lib import rcresolver


# Sample Usage method find_streams
# Pass url film or channel of the addon scraper to <rcresolver.Resolver()> class

result_dict_film = rcresolver.resolve('https://redecanais.cloud/trolls-2-dublado-2020-1080p_0df0e8cb8.html')
result_dict_tv = rcresolver.resolve('https://redecanaistv.com/assistir-premiere-2-online-24-horas-ao-vivo-1_9f269bd30.html')

# Usage

description = result_dict_film['desc']
player_url = result_dict_film['player']
video_url = result_dict_film['stream']

print('\nSTREAM FILME: ', video_url)

description = result_dict_tv['desc']
player_url = result_dict_tv['player']
video_url = result_dict_tv['stream']

print('\nSTREAM TV: ', video_url)

