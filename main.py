from data import Dataset
from flask import Flask, render_template, request, redirect
app = Flask(__name__)

@app.route("/")
def onboard():
    return render_template("onboard.html")

@app.route("/annotate")
def annotate():
    name = request.args.get('name')
    dataset = Dataset("sample.txt")
    dataset.prompt = ""
    return render_template("annotate.html", prompt=dataset.sentences[0], sentences=dataset.sentences[1:])

if __name__ == "__main__":
    app.run(port=8000, debug=True)