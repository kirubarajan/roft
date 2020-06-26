import json
import random
import copy

def generate_usernames(num_users):
    ''' Generates a num_users length list of random usernames based on descriptions of animals.
        (i.e. snobby_muskrat, orderly_spider). '''
    # Get adjectives from :
    # https://github.com/dariusk/corpora/raw/master/data/humans/descriptions.json
    # https://raw.githubusercontent.com/dariusk/corpora/master/data/humans/moods.json
    adjectives = set()
    with open('moods.json', 'r') as f:
        adjectives.update(json.load(f)['moods'])
    with open('descriptions.json', 'r') as f:
        adjectives.update(json.load(f)['descriptions'])

    # Add inappropriate words to remove here:
    adjectives.remove('molested')
    adjectives.remove('abused')

    # Get animals from :
    # https://raw.githubusercontent.com/dariusk/corpora/master/data/animals/collateral_adjectives.json
    # https://raw.githubusercontent.com/dariusk/corpora/master/data/animals/common.json
    animals = set()
    with open('collateral_adjectives.json', 'r') as f:
        animals.update([x['name'] for x in json.load(f)['animals']])
    with open('common.json', 'r') as f:
        animals.update(json.load(f)['animals'])

    # Number of animals should be 246
    # Number of adjectives should be 1018
    animals = list(animals)
    adjectives = list(adjectives)

    random.seed(99)
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
