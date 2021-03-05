from __future__ import print_function

import collections

import requests
import time
import os
import json
import argparse
import operator

JSON_COLUMNS = ['id', 'anticapitalism', 'baseThirst', 'buoyancy', 'chasiness', 'coldness', 'continuation', 'divinity', 'groundFriction', 'indulgence', 'laserlikeness', 'martyrdom', 'moxie', 'musclitude', 'bat', 'omniscience', 'overpowerment', 'patheticism', 'ruthlessness', 'shakespearianism', 'suppression', 'tenaciousness', 'thwackability', 'tragicness', 'unthwackability', 'watchfulness', 'pressurization', 'totalFingers', 'soul', 'deceased', 'peanutAllergy', 'cinnamon', 'fate', 'armor', 'ritual', 'blood', 'coffee', 'permAttr', 'seasAttr', 'weekAttr', 'gameAttr']
COLUMNS = ['team', 'league', 'division', 'name', 'position', 'turnOrder'] + JSON_COLUMNS + ["battingStars", "pitchingStars", "baserunningStars", "defenseStars"]


def get_stream_snapshot():
    snapshot = None
    response = requests.get("https://www.blaseball.com/events/streamData", stream=True)
    for line in response.iter_lines():
        snapshot = line
        break
    return json.loads(snapshot.decode("utf-8")[6:])


def get_team_leagues(snapshot):
    team_divisions = {}
    active_subleague_ids = snapshot['value']['leagues']['leagues'][0]['subleagues']
    active_subleagues = [subleague for subleague in snapshot['value']['leagues']['subleagues'] if subleague["id"] in active_subleague_ids]
    for subleague in active_subleagues:
        subleague_name = subleague["name"]
        division_ids = subleague["divisions"]
        divisions = [division for division in snapshot['value']['leagues']['divisions'] if division["id"] in division_ids]
        for division in divisions:
            division_name = division["name"]
            team_divisions.update({team_id: (subleague_name, division_name) for team_id in division["teams"]})
    return team_divisions


def batting_stars(player):
    return ((1 - float(player["tragicness"])) ** .01) * (float(player["buoyancy"]) ** 0) * (float(player["thwackability"]) ** .35) * (float(player["moxie"]) ** .075) * (float(player["divinity"]) ** .35) * (float(player["musclitude"]) ** .075) * ((1 - float(player["patheticism"])) ** .05) * (float(player["martyrdom"]) ** .02) * 5.0


def pitching_stars(player):
    return (float(player["shakespearianism"]) ** .1) * (float(player["suppression"]) ** 0) * (float(player["unthwackability"]) ** .5) * (float(player["coldness"]) ** .025) * (float(player["overpowerment"]) ** .15) * (float(player["ruthlessness"]) ** .4) * 5.0


def baserunning_stars(player):
    return (float(player["laserlikeness"]) ** .5) * (float(player["continuation"]) ** .1) * (float(player["baseThirst"]) ** .1) * (float(player["indulgence"]) ** .1) * (float(player["groundFriction"]) ** .1) * 5.0


def defense_stars(player):
    return (float(player["omniscience"]) ** .2) * (float(player["tenaciousness"]) ** .2) * (float(player["watchfulness"]) ** .1) * (float(player["anticapitalism"]) ** .1) * (float(player["chasiness"]) ** .1) * 5.0


def get_all_player_ids(snapshot):
    team_leagues = get_team_leagues(snapshot)
    allTeams = requests.get("https://blaseball.com/database/allTeams").json()
    player_ids = collections.defaultdict(lambda: {})
    for team in allTeams:
        positions = ('lineup', 'rotation', 'bench', 'bullpen')
        for position in positions:
            for turnOrder, player_id in enumerate(team[position]):
                league, division = team_leagues[team['id']] if team['id'] in team_leagues else ("N/A", "N/A")
                player_ids[team['id']][player_id] = [team['fullName'], league, division, None, position, turnOrder+1]
    return player_ids, 3, 4


BATCH_SIZE = 100


def generate_file(filename, inactive, archive, tournament):
    streamdata = get_stream_snapshot()
    if archive and os.path.isfile(filename):
        season_number = streamdata['value']['games']['season']['seasonNumber'] + 1  # 0-indexed, make 1-indexed
        day = streamdata['value']['games']['sim']['day'] + 2  # 0-indexed, make 1-indexed and add another if tomorrow
        os.rename(filename, filename.replace(".csv", "S{}preD{}.csv".format(season_number, day)))
    output = []
    all_player_ids, nameidx, positionidx = get_all_player_ids(streamdata)
    positions = ('lineup', 'rotation', 'bench', 'bullpen') if inactive else ('lineup', 'rotation')
    player_id_set = set()
    for team_players in all_player_ids.values():
        for player_id, player_data in team_players.items():
            if player_data[positionidx] in positions:
                player_id_set.add(player_id)
    player_id_list = list(player_id_set)
    while player_id_list:
        player_id_batch = player_id_list[:BATCH_SIZE]
        playerdata = requests.get("https://blaseball.com/database/players?ids={}".format(",".join(player_id_batch))).json()
        for player in playerdata:
            if player["deceased"]:
                continue
            player_id = player['id']
            team_id = player['tournamentTeamId'] if tournament else player['leagueTeamId']
            if not team_id:
                continue
            row = all_player_ids[team_id][player_id]
            row[nameidx] = player['name']
            row.extend([";".join(player[col]) if type(player[col]) == list else player[col] for col in JSON_COLUMNS])
            row.extend([starfunc(player) for starfunc in (batting_stars, pitching_stars, baserunning_stars, defense_stars)])
            output.append(row)
        player_id_list = player_id_list[BATCH_SIZE:]
        if player_id_list:
            time.sleep(10)
        
    output.sort(key=operator.itemgetter(0, 4, 5))
    with open(filename, 'w') as f:
        f.write("{}\n".format(",".join('"{}"'.format(col) for col in COLUMNS)))
        f.write("\n".join(",".join(['"{}"'.format(d) for d in datarow]) for datarow in output))


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='output.csv', help="output filepath")
    parser.add_argument('--inactive', help="include inactive players(bench/bullpen)", action='store_true')
    parser.add_argument('--archive', help="backup existing file before generating", action='store_true')
    parser.add_argument('--tournament', help="generate data for tournament teams", action='store_true')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = handle_args()
    generate_file(args.output, args.inactive, args.archive, args.tournament)
