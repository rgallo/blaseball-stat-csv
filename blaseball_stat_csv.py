from __future__ import print_function

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
    return ((1 - player["tragicness"]) ** .01) * (player["buoyancy"] ** 0) * (player["thwackability"] ** .35) * (player["moxie"] ** .075) * (player["divinity"] ** .35) * (player["musclitude"] ** .075) * ((1 - player["patheticism"]) ** .05) * (player["martyrdom"] ** .02) * 5.0


def pitching_stars(player):
    return (player["shakespearianism"] ** .1) * (player["suppression"] ** 0) * (player["unthwackability"] ** .5) * (player["coldness"] ** .025) * (player["overpowerment"] ** .15) * (player["ruthlessness"] ** .4) * 5.0


def baserunning_stars(player):
    return (player["laserlikeness"] ** .5) * (player["continuation"] ** .1) * (player["baseThirst"] ** .1) * (player["indulgence"] ** .1) * (player["groundFriction"] ** .1) * 5.0


def defense_stars(player):
    return (player["omniscience"] ** .2) * (player["tenaciousness"] ** .2) * (player["watchfulness"] ** .1) * (player["anticapitalism"] ** .1) * (player["chasiness"] ** .1) * 5.0


def get_all_player_ids(snapshot):
    team_leagues = get_team_leagues(snapshot)
    allTeams = requests.get("https://blaseball.com/database/allTeams").json()
    player_ids = {}
    for team in allTeams:
        positions = ('lineup', 'rotation', 'bench', 'bullpen')
        for position in positions:
            for turnOrder, player_id in enumerate(team[position]):
                player_ids[player_id] = [team['fullName'], team_leagues[team['id']][0], team_leagues[team['id']][1], None, position, turnOrder+1]
    return player_ids, 3, 4


BATCH_SIZE = 100


def generate_file(filename, inactive, archive):
    streamdata = get_stream_snapshot()
    if archive and os.path.isfile(filename):
        season_number = streamdata['value']['games']['season']['seasonNumber'] + 1  # 0-indexed, make 1-indexed
        day = streamdata['value']['games']['sim']['day'] + 2  # 0-indexed, make 1-indexed and add another if tomorrow
        os.rename(filename, filename.replace(".csv", "S{}preD{}.csv".format(season_number + 1, day)))
    output = []
    all_player_ids, nameidx, positionidx = get_all_player_ids(streamdata)
    positions = ('lineup', 'rotation', 'bench', 'bullpen') if inactive else ('lineup', 'rotation')
    player_id_list = [key for key, value in all_player_ids.items() if value[positionidx] in positions]
    while player_id_list:
        player_id_batch = player_id_list[:BATCH_SIZE]
        playerdata = requests.get("https://blaseball.com/database/players?ids={}".format(",".join(player_id_batch))).json()
        for player in playerdata:
            player_id = player['id']
            row = all_player_ids[player_id]
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
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = handle_args()
    generate_file(args.output, args.inactive, args.archive)
