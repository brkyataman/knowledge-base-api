from flask import Flask, jsonify, request
from flask import render_template
import os
import requests
import json
import pymysql


app = Flask(__name__)
source_path = r"C:/Users/beko/Desktop/random pubmed files"
processed_files_path = source_path + "/processed"
BIOPORTAL_URL = "http://data.bioontology.org"
BIOPORTAL_API_KEY = "f9ac9769-573d-4a6c-943a-5bafc350c91e"

def GetDbConnection():
    return pymysql.connect(host='localhost',
        user='root',
        password='pass',
        db='testdb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)


@app.route('/db')
def test_db():
    with GetDbConnection() as con:
        con.execute("SELECT * FROM tasks")
        rows = con.fetchall()

        result = "";
        for row in rows:
            result += str(row["task_id"]) + " " + str(row["title"]) + "\n"
        return result

@app.route('/')
def greetings():
    return render_template('greetings.html')


@app.route('/test', methods=["POST"])
def testfunc():
    data = request.json
    with GetDbConnection() as con:
        query = "UPDATE phrases SET noun_accuracy = %s where phrase_id = %s "
        args = (data["noun_accuracy"], data["phrase_id"])
        con.execute(query, args)
    return jsonify("done")


@app.route('/files')
@app.route('/files/<id>')
def files(id=None):
    if id is None:
        files = get_files()
        return render_template('files.html', files=files)
    else:
        noun_phrases = get_noun_phrases_from_db(int(id))
        #noun_phrases = get_noun_phrases_of_file(id + ".txt")
        return render_template("file_from_db.html", file_id=id, file_content=get_content(os.path.join(source_path, id + ".txt")), phrases=noun_phrases)


@app.route('/filePhrases/<id>')
def file_phrases(id):
        noun_phrases = get_noun_phrases_of_file(id + ".txt")
        return render_template('phrases_of_file.html', file_id=id, files=noun_phrases)


@app.route('/bioportal/search/<phrase>')
def search_phrase_in_bioportal(phrase):
        response = search_bioportal(phrase)
        ontologies=get_ontologies(phrase, response)
        ontologies = list(set(ontologies))
        return render_template('list_viewer.html', list=ontologies, length=len(ontologies), note=phrase)


def get_noun_phrases_from_db(article_id):

    with GetDbConnection() as con:
        query = "select a.article_id, p.*, apm.acc_value, p.noun_accuracy " \
                "from articles a " \
                "left join article_phrase_map apm on a.article_id = apm.article_id " \
                "left join phrases p on apm.phrase_id = p.phrase_id " \
                "WHERE a.article_id = %s;"
        args = (article_id)
        con.execute(query, args)
        rows = con.fetchall()
    return rows


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
        #result = search_bioportal(phrase)
        #ontologies = get_ontologies(phrase, result)
        ontologies = []
        phrase_list.append({'phrase': phrase, "ontologies": list(set(ontologies))})
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


def search_bioportal(term):
    params = {'q': term, "apikey": BIOPORTAL_API_KEY, "require_exact_match": "false"}
    r = requests.get(BIOPORTAL_URL + "/search", params=params)
    if r.status_code == 200:
        bioportal_obj = json.loads(r.text)
    return bioportal_obj


def get_ontologies(phrase, result):
    ontologies = []
    # result = search_bioportal(phrase)
    if result["collection"] is None:
        return ontologies
    for item in result["collection"]:
        if item["links"] is None or item["links"]["ontology"] is None:
            continue
        ontologies.append(item["links"]["ontology"])
    return ontologies

app.run(debug=True)