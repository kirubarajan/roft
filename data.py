"""Data Pre-Processing Helper Functions"""

class Dataset:
    def __init__(self, path):
        with open(path) as data:
            self.text = data.read()
            self.sentences = [sentence.strip() for sentence in self.text.split(".")]