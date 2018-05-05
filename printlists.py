if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, help='File to pretty print')
    args = parser.parse_args()

    format_string_prefix = u'{:2} {:'
    format_string_suffix = u'} {:3} {:5.3f} {:5.3f}'

    f = open(args.filename, 'r')
    import json
    data = json.load(f)

    top50 = data['top50']
    max_name_width = max([len(game[0]) for game in top50])
    format_string = format_string_prefix + str(max_name_width) + format_string_suffix
    print '[c]TOP 50'
    for idx, game in enumerate(top50):
        detail_string = format_string.format(idx + 1,
                game[0],
                game[2],
                game[3],
                game[4])
        print detail_string
    print '[/c]'

    bottom10 = data['bottom10']
    max_name_width = max([len(game[0]) for game in bottom10])
    format_string = format_string_prefix + str(max_name_width) + format_string_suffix
    print '[c]BOTTOM 10'
    for idx, game in enumerate(bottom10):
        detail_string = format_string.format(idx + 1,
                game[0],
                game[2],
                game[3],
                game[4])
        print detail_string
    print '[/c]'

    variable10 = data['variable10']
    print '[c]MOST VARIED'
    max_name_width = max([len(game[0]) for game in variable10])
    format_string = format_string_prefix + str(max_name_width) + format_string_suffix
    for idx, game in enumerate(variable10):
        detail_string = format_string.format(idx + 1,
                game[0],
                game[2],
                game[3],
                game[4])
        print detail_string
    print '[/c]'

    most10 = data['most10']
    print '[c]MOST RATED'
    max_name_width = max([len(game[0]) for game in most10])
    format_string = format_string_prefix + str(max_name_width) + format_string_suffix
    for idx, game in enumerate(most10):
        detail_string = format_string.format(idx + 1,
                game[0],
                game[2],
                game[3],
                game[4])
        print detail_string
    print '[/c]'
