if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, help='File to pretty print')
    args = parser.parse_args()

    f = open(args.filename, 'r')
    import json
    data = json.load(f)
    top50 = data['top50']
    print '[c]TOP 50'
    for idx, game in enumerate(top50):
        label = str(idx + 1) + '.'
        print label, game[0], game[2], game[3], game[4]
    print '[/c]'

    bottom10 = data['bottom10']
    print '[c]BOTTOM 10'
    for idx, game in enumerate(bottom10):
        label = str(idx + 1) + '.'
        print label, game[0], game[2], game[3], game[4]
    print '[/c]'

    variable10 = data['variable10']
    print '[c]MOST VARIED'
    for idx, game in enumerate(variable10):
        label = str(idx + 1) + '.'
        print label, game[0], game[2], game[3], game[4]
    print '[/c]'

    most10 = data['most10']
    print '[c]MOST RATED'
    for idx, game in enumerate(most10):
        label = str(idx + 1) + '.'
        print label, game[0], game[2], game[3], game[4]
    print '[/c]'
