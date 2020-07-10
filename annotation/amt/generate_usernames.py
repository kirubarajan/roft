import json, random, copy

'''
NOTE: You must run this script from within the amt directory. If you are importing and
calling generate_usernames as a function, make sure to run os.chdir(<path to amt directory>)

Adjectives Source:
https://github.com/dariusk/corpora/raw/master/data/humans/descriptions.json
https://raw.githubusercontent.com/dariusk/corpora/master/data/humans/moods.json

Animals Source:
https://raw.githubusercontent.com/dariusk/corpora/master/data/animals/collateral_adjectives.json
https://raw.githubusercontent.com/dariusk/corpora/master/data/animals/common.json'''

def generate_usernames(num_users):
    ''' Generates a num_users length list of random usernames based on descriptions of animals.
        (i.e. snobby_muskrat, orderly_spider).'''
    adjectives = set()
    with open('moods.json', 'r') as f:
        # https://raw.githubusercontent.com/dariusk/corpora/master/data/humans/moods.json
        adjectives.update(json.load(f)['moods'])
    with open('descriptions.json', 'r') as f:
        # https://github.com/dariusk/corpora/raw/master/data/humans/descriptions.json
        adjectives.update(json.load(f)['descriptions'])

    # Add inappropriate words to remove here:
    adjectives.remove('molested')
    adjectives.remove('abused')

    animals = set()
    with open('collateral_adjectives.json', 'r') as f:
        # https://raw.githubusercontent.com/dariusk/corpora/master/data/animals/collateral_adjectives.json
        animals.update([x['name'] for x in json.load(f)['animals']])
    with open('common.json', 'r') as f:
        # https://raw.githubusercontent.com/dariusk/corpora/master/data/animals/common.json
        animals.update(json.load(f)['animals'])

    animals = list(animals) # should be len 246
    adjectives = list(adjectives) # should be len 1018

    random.seed(99) # Reproducibility
    random.shuffle(animals)
    random.shuffle(adjectives)

    usernames = []
    for i in range(num_users):
      if i > len(adjectives):
        i -= len(adjectives)
        random.shuffle(adjectives)
      if i > len(animals):
        i -= len(animals)
        random.shuffle(animals)

      usernames.append('{}_{}'.format(adjectives[i], animals[i]).replace(' ', '_').lower())

    return usernames

def alliterate_usernames(animals, adjectives):
    ''' Generates a list of alliterated usernames, i.e. adored_antelope, feisty_fish
        from an input list of animals and adjectives.
        len(usernames) <= min(len(animals), len(adjectives))'''

    adjectives_copy = copy.deepcopy(list(adjectives))
    animals = list(animals)

    random.seed(99)
    random.shuffle(animals)
    random.shuffle(adjectives_copy)

    usernames = []
    for animal in animals:
      adjectives_with_letter = [a for a in adjectives_copy if a[0] == animal[0]]
      if len(adjectives_with_letter) > 0:
        adj = adjectives_with_letter[0]
        adjectives_copy.remove(adj)

      usernames.append('{}_{}'.format(adj, animal).replace(' ', '_').lower())

    return usernames
