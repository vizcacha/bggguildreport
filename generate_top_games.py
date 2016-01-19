# Get the top games for a BGG Guild
#
# This was written for pulling the top games from the Heavy Cardboard BGG Guild.
#
# TODO: Pydoc strings
# TODO: Refactor user retries
# TODO: Implement pastable report
# TODO: Remove dependency on boardgamegeek module to make better queries
#
# Steven Canning
# January 2016

from boardgamegeek import BoardGameGeek
from boardgamegeek.exceptions import BoardGameGeekAPIRetryError

import json
import math
import datetime

HEAVY_CARDBOARD = 2044

# Dictionary Keys
SORTED_GAMES = 'sorted_games'
SUMMARY = 'summary'
TOTAL_GAMES = 'total_games_rated'
GUILD_MEMBER_COUNT = 'guild_members'
FAILED_RETRIEVALS = 'failed_retrievals'
MEMBERS = 'members'
FAILED_USERS = 'failed_users'
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
        bgg = BoardGameGeek()

    guild = bgg.guild(guild_id)
    return guild.members

def get_user_ratings(username, bgg=None):
    """Returns a dict: (gameid, gamename) -> rating"""
    if bgg is None:
        bgg = BoardGameGeek()

    collection = bgg.collection(username)

    user_ratings = dict()
    for item in collection:
        if item.rating:
            user_ratings[(item.id, item.name)] = item.rating

    return user_ratings

def get_game_info(game_id, bgg=None):
    """Fetch the BGG info for game having game_id"""
    if bgg is None:
        bgg = BoardGameGeek()

    try:
        game = bgg.game(game_id=game_id)
    except BoardGameGeekAPIRetryError:
        game = None

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
        bgg = BoardGameGeek()

    guild_ratings = dict()
    try_again = list()
    third_try = list()
    failed_users = list()
    print 'Retrieving user ratings...'
    for member in members:
        try:
            user_ratings = get_user_ratings(member, bgg=bgg)
        except BoardGameGeekAPIRetryError:
            try_again.append(member)
            continue
        add_individual_to_group_ratings(guild_ratings, user_ratings)

    if try_again:
        print 'Failed to pull info for %d users. Retrying...' % len(try_again)
        for member in try_again:
            try:
                user_ratings = get_user_ratings(member, bgg=bgg)
            except BoardGameGeekAPIRetryError:
                third_try.append(member)
                continue
            add_individual_to_group_ratings(guild_ratings, user_ratings)

        if third_try:
            print 'Still failed to pull info for %d users. Final retry...' % len(third_try)
            for member in third_try:
                try:
                    user_ratings = get_user_ratings(member, bgg=bgg)
                except BoardGameGeekAPIRetryError:
                    failed_users.append(member)
                    continue
                add_individual_to_group_ratings(guild_ratings, user_ratings)

    if failed_users:
        print 'Failed to retrieve data for %d users' % len(failed_users)
        for user in failed_users:
            print user
    else:
        print 'Ratings retrieved for all users.'

    return guild_ratings, failed_users

def main(users=None, raw_data=None, generate_report=False):
    bgg = BoardGameGeek()

    # if not users and not raw_data: get users, get user ratings, process ratings
    # if users and not raw_data: load users, get user ratings, process ratings
    # if raw data: load users, load user ratings, process ratings

    now_str = str(datetime.datetime.now())
    filename_tag = '_'.join(now_str[:10].split())

    if raw_data is None:
        if users is None:
            members = get_guild_user_list(HEAVY_CARDBOARD, bgg=bgg)
            of = open('members_' + filename_tag + '.txt', 'w')
            for member in members:
                of.write(member + '\n')
        else:
            members = load_members_from_file(users)
        guild_size = len(members)
        print 'Members list loaded: %d guild members' % guild_size
        guild_ratings, failed_users = get_all_ratings(members, bgg=bgg)
        print 'Processing results...'
        print '%d games rated' % len(guild_ratings)
        top_games = list()
        for game_id, ratings in guild_ratings.iteritems():
            num_ratings = len(ratings)
            avg_rating = round(mean(ratings), 3)
            sd_ratings = round(stdev(ratings), 3)
            top_games.append((game_id[0], game_id[1], num_ratings, avg_rating, sd_ratings))

        # Sort the list
        top_games.sort(key=lambda x: x[2], reverse=True)

        # Write out the raw data to this point
        current_time_str = str(datetime.datetime.now())
        log_file = open('member_data_' + filename_tag + '.log', 'w')
        log_dict = dict()
        log_dict[SUMMARY] = { GUILD_MEMBER_COUNT: guild_size,
                              FAILED_RETRIEVALS: len(failed_users),
                              TOTAL_GAMES: len(guild_ratings),
                              TIME: current_time_str
                            }
        log_dict[MEMBERS] = members
        log_dict[FAILED_USERS] = failed_users
        log_dict[SORTED_GAMES] = top_games
        json.dump(log_dict, log_file)

    elif raw_data is not None:
        rating_data = json.load(open(raw_data, 'r'))
        top_games = rating_data[SORTED_GAMES]
        member_count = rating_data[SUMMARY][GUILD_MEMBER_COUNT]
        top_games = filter(lambda x: x[2] >= 0.1 * member_count, top_games)
        top_games.sort(key=lambda x: x[4], reverse=True)
        #of = open('summary.json', 'w')
        for game in top_games:
            print game[0], game[1], game[2], game[3], game[4]

    print 'Finished'

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--users', help='use provided list of users instead of pulling a new one')
    parser.add_argument('--raw', help='provide a .log file to regenerate the final data')
    parser.add_argument('-r', action='store_true', help='Generate pastable report. Does nothing right now')
    args = parser.parse_args()

    main(users=args.users, raw_data=args.raw, generate_report=args.r)
