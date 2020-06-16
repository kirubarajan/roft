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
pretraining_output_file_path = './processed/nyt-articles-train.txt'
dev_output_file_path = './processed/nyt-articles-dev.txt'
sampling_output_file_path = './processed/nyt-articles-test.txt'

def clean(text):
    return text.replace('\n', ' ').replace('\r', '') + '\n'

def get_outfile(filename):
    rng = random.random()
    if rng < 0.90:
        return pretraining_output_file_path
    elif rng < 0.95:
        return dev_output_file_path
    else:
        return sampling_output_file_path

def makedirs(filename):
    ''' https://stackoverflow.com/a/12517490 '''
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    return filename

if __name__ == '__main__':

    article_text = []
    if os.path.exists(nyt_corpus_file_location) and os.path.isdir(nyt_corpus_file_location):
        total_num_files = len(os.listdir(nyt_corpus_file_location))
        for index, filename in enumerate(os.listdir(nyt_corpus_file_location)):
            if filename.endswith('.ta.xml'):
                path = os.path.join(nyt_corpus_file_location, filename)
                with open(path, 'r+') as f:
                    data = json.load(f)
                    article_text.append(data['text'])
                print('Read in file {0}/{1}: {2}'.format(index, total_num_files, path))

    if len(article_text) > 1:
        with open(pretraining_output_file_path, 'w+') as train_outfile:
            with open(sampling_output_file_path, 'w+') as test_outfile:
                for article in article_text:
                    if random.random() > 0.80:
                        test_outfile.write(article.replace('\n', ' ').replace('\r', '') + '\n')
                    else:
                        train_outfile.write(article.replace('\n', ' ').replace('\r', '') + '\n')
