from blaseball_mike.models import League, SimulationData, Player
import os
import argparse
import operator
import json

INVERSE_STLATS = [
    "tragicness",
    "patheticism",
]  # These stlats are better for the target the smaller they are


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
]


def get_adjustment_stat(idx):
    return [
        "tragicness",
        "buoyancy",
        "thwackability",
        "moxie",
        "divinity",
        "musclitude",
        "patheticism",
        "martyrdom",
        "cinnamon",
        "base_thirst",
        "laserlikeness",
        "continuation",
        "indulgence",
        "ground_friction",
        "shakespearianism",
        "suppression",
        "unthwackability",
        "coldness",
        "overpowerment",
        "ruthlessness",
        "pressurization",
        "omniscience",
        "tenaciousness",
        "watchfulness",
        "anticapitalism",
        "chasiness",
    ][idx]


def handle_player_adjustments(player, adjustments):
    for adjustment in adjustments:
        if adjustment["type"] == 1:
            stlat_name = get_adjustment_stat(adjustment["stat"])
            if stlat_name in INVERSE_STLATS:
                setattr(
                    player,
                    stlat_name,
                    min(
                        max(getattr(player, stlat_name) + adjustment["value"], 0.001),
                        0.999,
                    ),
                )
            else:
                setattr(
                    player,
                    stlat_name,
                    max(getattr(player, stlat_name) + adjustment["value"], 0.001),
                )
    return player


def adjust_stlats_for_items(player):
    items = player.items
    player_copy = Player(player.json())
    for item in items:
        if item.health:
            player_copy = handle_player_adjustments(
                player_copy, item.root["adjustments"]
            )
            for section in ("root", "pre_prefix", "post_prefix", "suffix"):
                if getattr(item, section):
                    player_copy = handle_player_adjustments(
                        player_copy, getattr(item, section)["adjustments"]
                    )
            if item.prefixes:
                for prefix in item.prefixes:
                    player_copy = handle_player_adjustments(
                        player_copy, prefix["adjustments"]
                    )
            for category in ("defense", "hitting", "pitching", "baserunning"):
                setattr(
                    player_copy,
                    "_{}_rating".format(category),
                    max(
                        (getattr(player_copy, "_{}_rating".format(category)) or 0.001)
                        + (getattr(item, "{}_rating".format(category)) or 0.001),
                        0.001,
                    ),
                )
    return player_copy


def generate_file(filename, inactive, archive, include_items):
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
                        if include_items:
                            player = adjust_stlats_for_items(player)
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
    parser.add_argument(
        "--items", help="include item adjustments in stlats", action="store_true"
    )
    args = parser.parse_args()
    return args


def main():
    args = handle_args()
    generate_file(args.output, args.inactive, args.archive, args.items)


if __name__ == "__main__":
    main()
