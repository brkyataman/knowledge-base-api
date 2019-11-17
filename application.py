from flask import Flask
from flask import render_template
import os
app = Flask(__name__)
source_path = r"C:/Users/beko/Desktop/random pubmed files"
processed_files_path = source_path + "/processed"


@app.route('/')
def greetings():
    return render_template('greetings.html')


@app.route('/files')
@app.route('/files/<id>')
def files(id=None):
    if id is None:
        files = get_files()
        return render_template('files.html', files=files)
    else:
        noun_phrases = get_noun_phrases_of_file(id + ".txt")
        return render_template('file.html', file_id=id, file_content=get_content(os.path.join(source_path, id + ".txt")), phrases=noun_phrases)


@app.route('/filePhrases/<id>')
def file_phrases(id):
        noun_phrases = get_noun_phrases_of_file(id + ".txt")
        return render_template('phrases_of_file.html', file_id=id, files=noun_phrases)


def get_noun_phrases_of_file(filename):
    body = get_lines(os.path.join(processed_files_path, filename))
    tags = [line.rstrip().split("\t") for line in body]
    noun_phrases = []
    noun_phrase = []
    for tag in tags:
        if len(tag) < 3:
            continue
        if tag[3] == "B-NP":
            if len(noun_phrase) > 0:
                noun_phrases.append(noun_phrase)
                noun_phrase = []
            noun_phrase.append(tag)
        elif tag[3] == "I-NP":
            noun_phrase.append(tag)
        else:
            if len(noun_phrase) > 0:
                noun_phrases.append(noun_phrase)
                noun_phrase = []

    phrase_list = []
    for phrase_combo in noun_phrases:
        phrase = ""
        for item in phrase_combo:
            phrase += " " + item[0]
        phrase = phrase.strip()
        phrase_list.append(phrase)

    return phrase_list


def get_content(file_path):
    text = ""
    try:
        fp = open(file_path, "r")
        text = fp.read()
    finally:
        fp.close()
    return text


def get_lines(file_path):
    text = ""
    try:
        fp = open(file_path, "r")
        text = fp.readlines()
    finally:
        fp.close()
    return text

def get_files():
    files = os.listdir(processed_files_path)
    return [os.path.splitext(file)[0] for file in files]


app.run(debug=True)