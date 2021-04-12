from blaseball_mike.models import League, SimulationData, Player
import os
import argparse
import operator
import json

COLUMNS = [
    "team",
    "league",
    "division",
    "name",
    "position",
    "turnOrder",
    "id",
    "anticapitalism",
    "baseThirst",
    "buoyancy",
    "chasiness",
    "coldness",
    "continuation",
    "divinity",
    "groundFriction",
    "indulgence",
    "laserlikeness",
    "martyrdom",
    "moxie",
    "musclitude",
    "bat",
    "omniscience",
    "overpowerment",
    "patheticism",
    "ruthlessness",
    "shakespearianism",
    "suppression",
    "tenaciousness",
    "thwackability",
    "tragicness",
    "unthwackability",
    "watchfulness",
    "pressurization",
    "totalFingers",
    "soul",
    "deceased",
    "peanutAllergy",
    "cinnamon",
    "fate",
    "armor",
    "ritual",
    "blood",
    "coffee",
    "permAttr",
    "seasAttr",
    "weekAttr",
    "gameAttr",
    "battingStars",
    "pitchingStars",
    "baserunningStars",
    "defenseStars",
    "items",
]


def generate_file(filename, inactive, archive):
    sim = SimulationData.load()
    if archive and os.path.isfile(filename):
        os.rename(
            filename,
            filename.replace(".csv", "S{}preD{}.csv".format(sim.season, sim.day + 1)),
        )
    output = []
    positions = (
        ("lineup", "rotation", "bench", "bullpen")
        if inactive
        else ("lineup", "rotation")
    )
    league = League.load()
    players = Player.load_all()
    for subleague in league.subleagues.values():
        for division in subleague.divisions.values():
            for team in division.teams.values():
                for position in positions:
                    for turn_order, player_id in enumerate(
                        getattr(team, "_{}_ids".format(position))
                    ):
                        player = players[player_id]
                        player_row = [
                            team.full_name,
                            subleague.name,
                            division.name,
                            player.name,
                            position,
                            turn_order + 1,
                            player.id,
                            player.anticapitalism,
                            player.base_thirst,
                            player.buoyancy,
                            player.chasiness,
                            player.coldness,
                            player.continuation,
                            player.divinity,
                            player.ground_friction,
                            player.indulgence,
                            player.laserlikeness,
                            player.martyrdom,
                            player.moxie,
                            player.musclitude,
                            player.bat.id or "",
                            player.omniscience,
                            player.overpowerment,
                            player.patheticism,
                            player.ruthlessness,
                            player.shakespearianism,
                            player.suppression,
                            player.tenaciousness,
                            player.thwackability,
                            player.tragicness,
                            player.unthwackability,
                            player.watchfulness,
                            player.pressurization,
                            player.total_fingers,
                            player.soul,
                            player.deceased,
                            player.peanut_allergy,
                            player.cinnamon,
                            player.fate,
                            player.armor.id or "",
                            player.ritual,
                            player._blood_id,
                            player._coffee_id,
                            ";".join(attr.id for attr in player.perm_attr),
                            ";".join(attr.id for attr in player.seas_attr),
                            ";".join(attr.id for attr in player.week_attr),
                            ";".join(attr.id for attr in player.game_attr),
                            player.batting_rating * 5.0,
                            player.pitching_rating * 5.0,
                            player.baserunning_rating * 5.0,
                            player.defense_rating * 5.0,
                            json.dumps(player.items),
                        ]
                        output.append(player_row)
    output.sort(key=operator.itemgetter(0, 4, 5))
    with open(filename, "w") as f:
        f.write("{}\n".format(",".join('"{}"'.format(col) for col in COLUMNS)))
        f.write(
            "\n".join(
                ",".join(['"{}"'.format(d) for d in datarow]) for datarow in output
            )
        )


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output.csv", help="output filepath")
    parser.add_argument(
        "--inactive",
        help="include inactive players(bench/bullpen)",
        action="store_true",
    )
    parser.add_argument(
        "--archive", help="backup existing file before generating", action="store_true"
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = handle_args()
    generate_file(args.output, args.inactive, args.archive)
