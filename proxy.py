#!/usr/bin/env python3

from glob import glob
import json
import os

from flask import Flask, abort, jsonify, redirect, render_template, url_for


app = Flask(__name__)

app.jinja_env.add_extension("jinja2.ext.do")
app.jinja_env.add_extension("jinja2.ext.loopcontrols")


def load():
    loaded = json.load(open(os.getenv("GPEV_DATA")))
    data = {"communities": {}, "streams": {}, "users": {}, "aliases": {}, "posts": {}}

    def _add_post(post):
        uid = post["author"]["id"]
        if uid not in data["users"]:
            data["users"][uid] = dict(post["author"], type="PROFILE")
        if uid not in data["posts"]:
            data["posts"][uid] = {}
        if post.get("community"):
            cid = post["community"]["id"]
            if cid not in data["posts"]:
                data["posts"][cid] = {}
            if post["community"].get("stream"):
                sid = post["community"]["stream"]["id"]
                if sid not in data["posts"]:
                    data["posts"][sid] = {}
        if len(post["publicId"]) == 2:
            alias, pid = post["publicId"]
            if alias != uid:
                data["aliases"][alias[1:]] = uid
            data["posts"][uid][pid] = post
            if post.get("community"):
                data["posts"][cid][pid] = post
                if post["community"].get("stream"):
                    data["posts"][sid][pid] = post
        elif len(post["publicId"]) == 1 and post["publicId"][0].startswith("events/"):
            pass  # TODO
        else:
            raise ValueError(post)

    for acc in loaded["accounts"]:
        data["users"][acc["id"]] = {k: acc[k] for k in ("id", "name", "image", "type")}
        data["posts"][acc["id"]] = {}
        for post in acc["posts"]:
            _add_post(post)
        for comm in acc["communities"]:
            data["communities"][comm["id"]] = {k: comm[k] for k in ("id", "name", "image", "tagline")}
            data["streams"][comm["id"]] = {}
            for cat in comm["categories"]:
                data["streams"][comm["id"]][cat["id"]] = {k: cat[k] for k in ("id", "name")}
                for post in cat["posts"]:
                    _add_post(post)

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
