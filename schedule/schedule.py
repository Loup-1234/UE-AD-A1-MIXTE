from flask import Flask, request, jsonify, make_response
import json
import os
import requests

app = Flask(__name__)

PORT = 3202
HOST = '0.0.0.0'
MOVIE_SERVICE_URL = os.environ.get("MOVIE_SERVICE_URL", "http://127.0.0.1:3001/graphql")

MOVIE_QUERY = """
query GetMovie($id: String!) {
    movie_with_id(_id: $id) {
        id
        title
        director
        rating
        actors {
            id
            firstname
            lastname
            birthyear
            films
        }
    }
}
"""

with open('{}/data/times.json'.format("."), "r") as jsf:
    schedule = json.load(jsf)["schedule"]


def write(schedule_list):
    with open('{}/data/times.json'.format("."), "w") as f:
        json.dump({"schedule": schedule_list}, f, indent=2)


def is_admin():
    return request.headers.get("X-Admin", "").lower() == "true"


def fetch_movie(movieid):
    """Interroge le service Movie (GraphQL). Retourne (movie_or_none, service_ok)."""
    try:
        resp = requests.post(
            MOVIE_SERVICE_URL,
            json={"query": MOVIE_QUERY, "variables": {"id": movieid}},
            timeout=5
        )
        if resp.status_code != 200:
            return None, False
        payload = resp.json()
        if payload.get("errors"):
            return None, False
        return payload.get("data", {}).get("movie_with_id"), True
    except (requests.RequestException, ValueError):
        return None, False


@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Showtime service!</h1>", 200)


@app.route("/json", methods=['GET'])
def get_json():
    return make_response(jsonify(schedule), 200)


@app.route("/schedule/<movieid>", methods=['GET'])
def get_schedule_byid(movieid):
    movie_dates = [
        showtime["date"]
        for showtime in schedule
        if movieid in showtime.get("movies", [])
    ]

    if movie_dates:
        return make_response(jsonify(movie_dates), 200)

    return make_response(jsonify({"error": "Movie ID not found"}), 404)


@app.route("/schedule/date/<date>", methods=['GET'])
def get_schedule_by_date(date):
    for showtime in schedule:
        if showtime.get("date") == date:
            return make_response(jsonify(showtime), 200)

    return make_response(jsonify({"error": "Date not found"}), 404)


@app.route("/schedule/date/<date>/details", methods=['GET'])
def get_schedule_date_details(date):
    showtime = next((s for s in schedule if s.get("date") == date), None)
    if not showtime:
        return make_response(jsonify({"error": "Date not found"}), 404)

    detailed_movies = []
    for movieid in showtime.get("movies", []):
        movie, service_ok = fetch_movie(movieid)
        if not service_ok:
            return make_response(jsonify({"error": "Movie service unavailable"}), 503)
        if movie:
            detailed_movies.append(movie)
        else:
            detailed_movies.append({"id": movieid, "error": "Movie details not found"})

    return make_response(jsonify({"date": date, "movies": detailed_movies}), 200)


@app.route("/schedule/<movieid>", methods=['POST'])
def add_schedule(movieid):
    if not is_admin():
        return make_response(jsonify({"error": "Admin privileges required"}), 403)

    req = request.get_json(silent=True)
    if not req or not req.get("date"):
        return make_response(jsonify({"error": "Invalid payload: 'date' is required"}), 400)

    date = str(req["date"])

    # Vérifie auprès du service Movie (GraphQL) que le film existe.
    movie, service_ok = fetch_movie(movieid)
    if not service_ok:
        return make_response(jsonify({"error": "Movie service unavailable"}), 503)
    if not movie:
        return make_response(jsonify({"error": "Movie ID not found in Movie service"}), 404)

    for showtime in schedule:
        if showtime.get("date") == date:
            if movieid in showtime["movies"]:
                return make_response(jsonify({"error": "Movie already scheduled on this date"}), 409)
            showtime["movies"].append(movieid)
            write(schedule)
            return make_response(jsonify({"message": "Schedule added successfully"}), 200)

    schedule.append({"date": date, "movies": [movieid]})
    write(schedule)
    return make_response(jsonify({"message": "Schedule added successfully"}), 200)


@app.route("/schedule/<movieid>", methods=['DELETE'])
def delete_schedule(movieid):
    if not is_admin():
        return make_response(jsonify({"error": "Admin privileges required"}), 403)

    target_date = request.args.get("date")
    removed = False

    for showtime in list(schedule):
        if target_date and showtime.get("date") != target_date:
            continue
        if movieid in showtime.get("movies", []):
            showtime["movies"].remove(movieid)
            removed = True
            if not showtime["movies"]:
                schedule.remove(showtime)

    if not removed:
        return make_response(jsonify({"error": "Schedule entry not found for this movie"}), 404)

    write(schedule)
    return make_response(jsonify({"message": "Schedule deleted successfully"}), 200)


if __name__ == "__main__":
    print("Server running in port %s" % PORT)
    app.run(host=HOST, port=PORT)
