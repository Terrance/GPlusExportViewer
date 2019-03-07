#!/usr/bin/env python3

from glob import glob
import json
import os.path

from flask import Flask, jsonify, render_template


app = Flask(__name__)
app.jinja_env.add_extension("jinja2.ext.do")
app.jinja_env.add_extension("jinja2.ext.loopcontrols")


def names():
    paths = glob("data/*.json")
    return [path[5:-5] for path in paths]


def content(name):
    return json.load(open(os.path.join("data", "{}.json".format(name))))


@app.route("/")
def index():
    return render_template("index.j2", names=names())


@app.route("/view/<name>")
def view(name):
    return render_template("view.j2", content=content(name))


@app.route("/raw/<name>")
def raw(name):
    return jsonify(content(name))


if __name__ == "__main__":
    app.run(debug=True)
