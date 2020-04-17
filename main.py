from data import Dataset
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def index():
    dataset = Dataset("sample.txt")
    dataset.prompt = ""
    return render_template("index.html", prompt=dataset.sentences[0], sentences=dataset.sentences[1:])

if __name__ == "__main__":
    app.run(port=8000, debug=True)