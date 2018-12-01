# Get the top games for a BGG Guild
#
# This was written for pulling the top games from the Heavy Cardboard BGG Guild.
#
# TODO: Pydoc strings
# TODO: Refactor user retries
# TODO: Implement pastable report
# TODO: Remove dependency on boardgamegeek module to make better queries

from boardgamegeek import BGGClient

from Queue import Queue
import json
import csv
import math
import datetime
import yaml

HEAVY_CARDBOARD = 2044
PUNCHING_CARDBOARD = 1805

# Dictionary Keys
SORTED_GAMES = 'sorted_games'
SUMMARY = 'summary'
TOTAL_GAMES = 'total_games_rated'
GUILD_MEMBER_COUNT = 'guild_members'
MEMBERS = 'members'
TIME = 'time_at_generation'

### UTILITY FUNCTIONS ###

def mean(numbers):
    """Return the arithmetic mean of a list of numbers"""
    return float(sum(numbers)) / float(len(numbers))

def stdev(numbers):
    """Return the population standard deviation of a list of numbers"""
    avg = mean(numbers)
    variance = mean(map(lambda x: (x - avg)**2, numbers))
    return math.sqrt(variance)

### Functions that fetch from BGG ###

def get_guild_user_list(guild_id, bgg=None):
    """Fetch the member list for a BGG Guild"""
    if bgg is None:
        bgg = BGGClient()

    print 'Fetching guild user list'
    guild = bgg.guild(guild_id)
    return list(guild.members)

def get_user_ratings(username, bgg=None):
    """Returns a dict: gameid -> rating"""
    if bgg is None:
        bgg = BGGClient()

    collection = bgg.collection(username)

    user_ratings = dict()
    for item in collection:
        if item.rating:
            user_ratings[item.id] = item.rating

    return user_ratings

def get_game_info(game_id, bgg=None):
    """Fetch the BGG info for game having game_id"""
    if bgg is None:
        bgg = BGGClient()

    print 'Fetching info for game', str(game_id)

    game = None
    while game is None:
        try:
            game = bgg.game(game_id=game_id)
        except Exception:
            print 'Trying to fetch again...'
            continue

    return game

def add_individual_to_group_ratings(master_dict, user_dict):
    """Combine a user's ratings with the overall ratings"""
    for game, rating in user_dict.iteritems():
        if game in master_dict:
            master_dict[game].append(rating)
        else:
            master_dict[game] = [rating]

def load_members_from_file(filename):
    members = list()
    fi = open(filename, 'r')
    for line in fi.readlines():
        members.append(line.strip())

    return members

def get_all_ratings(members, bgg=None):
    """Get the ratings for all users in the list members.

        Returns: A dict (gameid, game name) -> list of ratings
    """
    if bgg is None:
        bgg = BGGClient()

    all_member_ratings = dict()

    print 'Retrieving user ratings...'
    work_queue = Queue()
    for member in members:
        work_queue.put(member)

    while not work_queue.empty():
        print work_queue.qsize(), 'members to process'
        member = work_queue.get()
        print 'Fetching data for ', member
        try:
            user_ratings = get_user_ratings(member, bgg=bgg)
        except Exception:
            work_queue.put(member)
            continue
        all_member_ratings[member] = user_ratings

    print 'Ratings retrieved for all users.'

    return all_member_ratings

def collapse_ratings(member_ratings):
    guild_ratings = dict()
    for _, ratings in member_ratings.iteritems():
        add_individual_to_group_ratings(guild_ratings, ratings)
    return guild_ratings

def main(users=None, raw_data=None, generate_report=False, prune=None):
    bgg = BGGClient()

    # if not users and not raw_data: get users, get user ratings, process ratings
    # if users and not raw_data: load users, get user ratings, process ratings
    # if raw data: load users, load user ratings, process ratings

    now_str = str(datetime.datetime.now())
    filename_tag = '_'.join(now_str[:10].split())

    if raw_data is None:
        # load members from file or query for current list
        if users is None:
            members = get_guild_user_list(PUNCHING_CARDBOARD, bgg=bgg)
            of = open('members_' + filename_tag + '.txt', 'w')
            for member in members:
                of.write(member + '\n')
        else:
            members = load_members_from_file(users)

        guild_size = len(members)
        print 'Members list loaded: %d guild members' % guild_size
        member_ratings = get_all_ratings(members, bgg=bgg)
        guild_ratings = collapse_ratings(member_ratings)

        print 'Processing results...'
        print '%d games rated' % len(guild_ratings)
        top_games = list()
        for game_id, ratings in guild_ratings.iteritems():
            num_ratings = len(ratings)
            avg_rating = round(mean(ratings), 3)
            sd_ratings = round(stdev(ratings), 3)
            top_games.append((game_id, num_ratings, avg_rating, sd_ratings))

        # Sort the list
        top_games.sort(key=lambda x: x[2], reverse=True)

        # Write out the raw data to this point
        current_time_str = str(datetime.datetime.now())
        rating_data = dict()
        rating_data[SUMMARY] = { GUILD_MEMBER_COUNT: guild_size,
                              TOTAL_GAMES: len(guild_ratings),
                              TIME: current_time_str
                            }
        rating_data[MEMBERS] = members
        rating_data[SORTED_GAMES] = top_games
        with open('guild_data_' + filename_tag + '.json', 'w') as raw_data_file:
            json.dump(rating_data, raw_data_file)
        with open('member_data_' + filename_tag + '.yml', 'w') as raw_data_file:
            yaml.dump(member_ratings, raw_data_file)

    elif raw_data is not None:
        rating_data = json.load(open(raw_data, 'r'))

    # Either path we now have rating_data
    top_games = rating_data[SORTED_GAMES]
    member_count = rating_data[SUMMARY][GUILD_MEMBER_COUNT]

    # If we want to prune the games
    if prune is not None:
        pruned_games = list()
        with open(prune, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                gameid = int(row[0])
                matches = [x for x in top_games if x[0] == gameid]
                if len(matches) == 1:
                    match = matches[0]
                    matched_game = (row[1], match[0], match[1], match[2], match[3])
                elif len(matches) == 0:
                    matched_game = (row[1], gameid, 0, 0, 0)
                else:
                    print 'ERROR'
                    return
                pruned_games.append(matched_game)
        pruned_games.sort(key=lambda x: x[3], reverse=True)
        
        max_name_width = max([len(game[0]) for game in pruned_games])
        format_string_prefix = u'{:2} {:'
        format_string_suffix = u'} {:3} {:5.3f} {:5.3f}'
        format_string = format_string_prefix + str(max_name_width) + format_string_suffix
        for idx, game in enumerate(pruned_games):
            detail_string = format_string.format(idx + 1,
                    game[0],
                    game[2],
                    game[3],
                    game[4])
            print detail_string
        return
    else:
        top_games = filter(lambda x: x[1] >= 0.1 * member_count, top_games)

    # Get the top 50
    top50 = list()
    top_games.sort(key=lambda x: x[2], reverse=True)
    count_of_printed = 0
    for game in top_games:
        game_info = get_game_info(game[0], bgg)
        if not game_info.expansion:
            count_of_printed += 1
            top50.append((game_info.name, game[0], game[1], game[2], game[3]))
        if count_of_printed > 49:
            break

    # Get the bottom 10
    bottom10 = list()
    top_games.sort(key=lambda x: x[2])
    count_of_printed = 0
    for game in top_games:
        game_info = get_game_info(game[0], bgg)
        if not game_info.expansion:
            count_of_printed += 1
            bottom10.append((game_info.name, game[0], game[1], game[2], game[3]))
        if count_of_printed > 9:
            break

    # Get the most variable
    variable10 = list()
    top_games.sort(key=lambda x: x[3], reverse=True)
    count_of_printed = 0
    for game in top_games:
        game_info = get_game_info(game[0], bgg)
        if not game_info.expansion:
            count_of_printed += 1
            variable10.append((game_info.name, game[0], game[1], game[2], game[3]))
        if count_of_printed > 9:
            break

    # Get the most rated
    most10 = list()
    top_games.sort(key=lambda x: x[1], reverse=True)
    count_of_printed = 0
    for game in top_games:
        game_info = get_game_info(game[0], bgg)
        if not game_info.expansion:
            count_of_printed += 1
            most10.append((game_info.name, game[0], game[1], game[2], game[3]))
        if count_of_printed > 9:
            break

    fi = open('lists_' + filename_tag + '.json', 'w')
    lists_dict = dict()
    lists_dict['top50'] = top50
    lists_dict['bottom10'] = bottom10
    lists_dict['variable10'] = variable10
    lists_dict['most10'] = most10
    json.dump(lists_dict, fi)

    print 'Finished'

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--users', help='use provided list of users instead of pulling a new one')
    parser.add_argument('--raw', help='provide a .log file to regenerate the final data')
    parser.add_argument('--prune', help='Prune raw data to a specific list of games')
    parser.add_argument('--n', type=int, help='Give the top n games')
    parser.add_argument('-r', action='store_true', help='Generate pastable report. Does nothing right now')
    args = parser.parse_args()

    main(users=args.users, raw_data=args.raw, generate_report=args.r, prune=args.prune)
