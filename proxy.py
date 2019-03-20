#!/usr/bin/env python3

from collections import defaultdict
from glob import glob
import json
import os

from flask import Flask, abort, jsonify, redirect, render_template, url_for


app = Flask(__name__)

app.jinja_env.add_extension("jinja2.ext.do")
app.jinja_env.add_extension("jinja2.ext.loopcontrols")


def load():
    app.logger.debug("Starting data load")
    loaded = json.load(open(os.getenv("GPEV_DATA")))
    data = {"users": {},
            "aliases": {},
            "collections": {},
            "communities": {},
            "streams": defaultdict(dict),
            "posts": defaultdict(dict)}

    def _add_post(post, *keys):
        uid = post["author"]["id"]
        if uid not in data["users"]:
            data["users"][uid] = dict(post["author"], type="PROFILE")
        if len(post["publicId"]) == 2:
            alias, pid = post["publicId"]
            if alias != uid:
                data["aliases"][alias[1:]] = uid
            data["posts"][uid][pid] = post
            for key in keys:
                data["posts"][key][pid] = post
        elif len(post["publicId"]) == 1 and post["publicId"][0].startswith("events/"):
            pass  # TODO
        else:
            raise ValueError(post)

    for acc in loaded["accounts"]:
        app.logger.debug("Account: %s", acc["id"])
        data["users"][acc["id"]] = {k: acc[k] for k in ("id", "name", "image", "type")}
        for post in acc["posts"]:
            _add_post(post)
        for coll in acc["collections"]:
            app.logger.debug("Collection: %s", coll["id"])
            data["collections"][coll["id"]] = {k: coll[k] for k in ("id", "name", "image", "type")}
            for post in coll["posts"]:
                _add_post(post, coll["id"])
                data["posts"][coll["id"]][post["publicId"][1]] = post
        for comm in acc["communities"]:
            app.logger.debug("Community: %s", comm["id"])
            data["communities"][comm["id"]] = {k: comm[k] for k in ("id", "name", "image", "tagline")}
            for cat in comm["categories"]:
                data["streams"][comm["id"]][cat["id"]] = {k: cat[k] for k in ("id", "name")}
                for post in cat["posts"]:
                    _add_post(post, comm["id"], cat["id"])

    return data


data = load()


@app.route("/")
def index():
    return render_template("proxy.j2")


@app.route("/<uid>")
def profile(uid):
    if uid[1:] in data["aliases"]:
        return redirect(url_for("profile", uid=data["aliases"][uid[1:]]))
    try:
        user = data["users"][uid]
        posts = data["posts"][uid]
    except KeyError:
        abort(404)
    return render_template("profile.j2", user=user, posts=posts.values())


@app.route("/collection/<cid>")
def collection(cid):
    try:
        coll = data["collections"][cid]
        posts = data["posts"][cid]
    except KeyError:
        abort(404)
    return render_template("collection.j2", coll=coll, posts=posts.values())


@app.route("/<uid>/posts/<pid>")
def post(uid, pid):
    if uid[1:] in data["aliases"]:
        return redirect(url_for("post", uid=data["aliases"][uid[1:]], pid=pid))
    try:
        user = data["users"][uid]
        post = data["posts"][uid][pid]
    except KeyError:
        abort(404)
    return render_template("profile.j2", user=user, posts=[post])


@app.route("/communities/<cid>")
def community(cid):
    try:
        comm = data["communities"][cid]
        posts = data["posts"][cid]
    except KeyError:
        abort(404)
    return render_template("community.j2", comm=comm, posts=posts.values())


@app.route("/communities/<cid>/stream/<sid>")
def stream(cid, sid):
    try:
        comm = data["communities"][cid]
        data["streams"][cid][sid]
        posts = data["posts"][sid]
    except KeyError:
        abort(404)
    return render_template("community.j2", comm=comm, posts=posts.values())


@app.route("/raw")
def raw():
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
