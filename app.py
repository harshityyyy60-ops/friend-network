import os
from flask import Flask, render_template, request, redirect, url_for
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
driver = GraphDatabase.driver(URI, auth=AUTH)


def run_query(query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


@app.route("/")
def index():
    users = run_query("MATCH (u:User) RETURN u.name AS name ORDER BY name")
    edges = run_query(
        """
        MATCH (a:User)-[:FRIEND]->(b:User)
        RETURN a.name AS source, b.name AS target
        """
    )
    return render_template(
        "index.html",
        users=[u["name"] for u in users],
        edges=edges,
        mutuals=None,
        selected_pair=None,
    )


@app.route("/add-user", methods=["POST"])
def add_user():
    name = request.form.get("name", "").strip()
    if name:
        run_query("MERGE (:User {name: $name})", {"name": name})
    return redirect(url_for("index"))


@app.route("/add-friend", methods=["POST"])
def add_friend():
    user1 = request.form.get("user1", "").strip()
    user2 = request.form.get("user2", "").strip()
    if user1 and user2 and user1 != user2:
        run_query(
            """
            MATCH (a:User {name: $user1}), (b:User {name: $user2})
            MERGE (a)-[:FRIEND]-(b)
            """,
            {"user1": user1, "user2": user2},
        )
    return redirect(url_for("index"))


@app.route("/mutual-friends", methods=["POST"])
def mutual_friends():
    user1 = request.form.get("m_user1", "").strip()
    user2 = request.form.get("m_user2", "").strip()
    users = run_query("MATCH (u:User) RETURN u.name AS name ORDER BY name")
    edges = run_query(
        """
        MATCH (a:User)-[:FRIEND]->(b:User)
        RETURN a.name AS source, b.name AS target
        """
    )
    mutuals = []
    if user1 and user2 and user1 != user2:
        rows = run_query(
            """
            MATCH (u1:User {name: $user1})-[:FRIEND]-(mutual:User)-[:FRIEND]-(u2:User {name: $user2})
            RETURN DISTINCT mutual.name AS name ORDER BY name
            """,
            {"user1": user1, "user2": user2},
        )
        mutuals = [r["name"] for r in rows]
    return render_template(
        "index.html",
        users=[u["name"] for u in users],
        edges=edges,
        mutuals=mutuals,
        selected_pair=(user1, user2),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
