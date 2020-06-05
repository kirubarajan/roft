'''
    Script to parse out the raw text of articles from the NYT Articles Corpus

    This script will look for a directory named raw and find any .ta.xml
    files inside, parse out the "text" field in the file and then write the text out
    to a file named "nyt-articles.txt" with <|startofarticle|> and <|endofarticle|>
    tags surrounding the edges of each article
'''

import os, json
import xml.etree.ElementTree as xml

nyt_corpus_file_location = './raw'
output_file_path = './nyt-articles.txt'

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
        with open(output_file_path, 'w+') as outfile:
            for article in article_text:
                outfile.write('<|startofarticle|>' + article + '<|endofarticle|>')
