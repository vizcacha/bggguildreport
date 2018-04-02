import yaml
from boardgamegeek import BGGClient

def main(user, member_data_file):
    bgg = BGGClient()

    with open(member_data_file, 'r') as data_file:
        member_data = yaml.load(data_file)

    user_data = member_data[user]
    del member_data[user]
    user_collection_size = len(user_data)

    member_scores = list()
    for user, ratings in member_data.iteritems():
        score = 0
        games_in_common = 0
        for game, rating in user_data.iteritems():
            if game in ratings:
                diff = (rating - ratings[game])**2
                score += diff
                games_in_common += 1
        member_scores.append({'user': user, 'score': score, 'common': games_in_common})

    member_scores = filter(lambda x: x['common'] >= 0.5 * user_collection_size, member_scores)
    member_scores.sort(key=lambda x: x['score'])

    filename = user + '_followers.yml'
    with open(filename, 'w') as fo:
        yaml.dump(member_scores, fo)

    for i in range(5):
        member = member_scores[i]
        print member['user'], member['score'], member['common']


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user')
    parser.add_argument('--member-data')
    args = parser.parse_args()
    main(args.user, args.member_data)
