'''
    Script to parse out the raw text of articles from the Reddit Writing Prompts Corpus

    This script will look for a directory named raw and find any .wp_target
    files inside, detokenize it, strip all newlines and carriage returns from
    the raw text and then write the text out, one story per line
    to two files in an 80/20 split named "reddit-stories-train.txt" and
    "reddit-stories-test.txt"
'''

import os, random
from sacremoses import MosesDetokenizer
import xml.etree.ElementTree as xml

corpus_location = './raw'
pretraining_output_file_path = './processed/reddit-stories-train.txt'
dev_output_file_path = './processed/reddit-stories-dev.txt'
sampling_output_file_path = './processed/reddit-stories-test.txt'

def clean(text):
  tokens = text.split(' ')
  tokens = [t.replace('<newline>', '\n').replace('``', '"').replace("''", '"') for t in tokens]
  detoked_string = ''.join(MosesDetokenizer().detokenize(tokens)).replace('\n', ' ').replace('\r', '') + '\n'
  return detoked_string

def determine_outfile(filename):
    if 'train' in filename:
        return pretraining_output_file_path
    else:
        if random.random() < 0.50:
            return dev_output_file_path
        else:
            return sampling_output_file_path

if __name__ == '__main__':
    if os.path.exists(corpus_location) and os.path.isdir(corpus_location):
        for index, filename in enumerate(os.listdir(corpus_location)):
            if filename.endswith('.wp_target'):
                print("Processing " + filename)
                path = os.path.join(corpus_location, filename)
                outfile = determine_outfile(filename)

                with open(path, 'r+') as f:
                    with open(outfile, 'w+') as out_f:
                        for index, line in enumerate(f):
                            out_f.write(clean(line))
                            print('Wrote Story #{0} of file {1}'.format(str(index), filename))
