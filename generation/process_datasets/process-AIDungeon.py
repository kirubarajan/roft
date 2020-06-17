'''
    Script to parse out stories from the Text Adventures Corpus

    This script will look for a directory named raw and find the three files
    inside called text_adventures_[train/dev/test].txt. It will then regex parse
    for the <|startoftext|> and <|endoftext|> delimiters, strip newlines and
    carriage returns from the text contained within and output that text
    one text adventure per line to two files in an 80/20 split named
    "ai-dungeon-test.txt" and "ai-dungeon-train.txt"
'''

import os, re, mmap
import xml.etree.ElementTree as xml

corpus_location = './raw'
pretraining_output_file_path = './processed/ai-dungeon-train.txt'
dev_output_file_path = './processed/ai-dungeon-dev.txt'
sampling_output_file_path = './processed/ai-dungeon-test.txt'

# Regex to grab all text between <|startoftext|> and <|endoftext|>
pattern = re.compile(b'<\|startoftext\|\>((.|\n)*?)\<\|endoftext\|\>')

def clean(text):
    return text.replace('\n', ' ').replace('\r', '') + '\n'

def get_outfile(filename):
    if 'train' in filename:
        return pretraining_output_file_path
    elif 'dev' in filename:
        return dev_output_file_path
    elif 'test' in filename:
        return sampling_output_file_path
    else:
        print('Error: input file ' + filename + ' not train dev or test split')
        exit(-1)

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
    if os.path.exists(corpus_location) and os.path.isdir(corpus_location):
        for filename in os.listdir(corpus_location):
            if filename.endswith('.txt'):
                path = os.path.join(corpus_location, filename)
                outfile = get_outfile(filename)
                stories_written = 0
                with open(path, 'r+b') as f:
                    with open(makedirs(outfile), 'a+') as out_f:
                        data = mmap.mmap(f.fileno(), 0)
                        for m in re.finditer(pattern, data):
                            out_f.write(clean(str(m.group(1),'utf-8','ignore')))
                            stories_written += 1
                            print('Wrote Story #{0} of file {1}'.format(
                                str(stories_written), filename))
