'''
    Script to parse out the raw text of articles from the NYT Articles Corpus

    This script will look for a directory named raw and find any .ta.xml
    files inside, parse out the "text" field in the file, strip all newlines and
    carriage returns from the file and then write the text out, one article per line
    to two files in an 80/20 split named "nyt-articles-test.txt" and
    "nyt-articles-train.txt"
'''

import os, json, random
import xml.etree.ElementTree as xml

corpus_location = './raw'
pretraining_output_file_path = './nyt-articles-train.txt'
sampling_output_file_path = './nyt-articles-test.txt'

def clean(text):
    return text.replace('\n', ' ').replace('\r', '') + '\n'

def get_outfile(filename):
    if random.random() < 0.80:
        return pretraining_output_file_path
    else:
        return sampling_output_file_path

if __name__ == '__main__':
    if os.path.exists(corpus_location) and os.path.isdir(corpus_location):
        num_files = len(os.listdir(corpus_location))
        for index, filename in enumerate(os.listdir(corpus_location)):
            if filename.endswith('.ta.xml'):
                path = os.path.join(corpus_location, filename)
                with open(path, 'r+') as f:
                    article = json.load(f)['text']
                    if len(article) > 1:
                        outfile = get_outfile(filename)
                        with open(outfile, 'a+') as out_f:
                            out_f.write(clean(data['text']))
                            print('Wrote Article #{0}/{1} to file {2}'.format(
                                str(index), str(num_files), outfile))
