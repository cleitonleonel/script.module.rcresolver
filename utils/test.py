# -*- coding: utf-8 -*-
#
import json
from lib import rcresolver

# Sample Usage method find_streams
# Pass url film or channel of the addon scraper to <rcresolver.Resolver()> class

result_dict_film = rcresolver.resolve(
    'https://redecanais.cloud/velozes-furiosos-9-dublado-2021-1080p_5051fb7cf.html'
)

print(json.dumps(result_dict_film, indent=4))

# result_dict_tv = rcresolver.resolve(
# 'https://redecanaistv.com/assistir-premiere-2-online-24-horas-ao-vivo-1_9f269bd30.html'
# )

# Usage

description = result_dict_film['description']
player_url = result_dict_film['player']
video_url = result_dict_film['download']
player_referer = result_dict_film['referer']

# print('\nSTREAM FILME: ', video_url)
# print('\nURL_PLAYER: ', player_url)
# print('\nPLAYER REFERER: ', player_referer)

# description = result_dict_tv['desc']
# player_url = result_dict_tv['player']
# video_url = result_dict_tv['stream']

# print(result_dict_tv)
# print('\nSTREAM TV: ', video_url)
