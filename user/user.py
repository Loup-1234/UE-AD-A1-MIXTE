from flask import Flask, request, jsonify, make_response
import json
import os
import requests

app = Flask(__name__)

PORT = 3203
HOST = '0.0.0.0'
BOOKING_SERVICE_URL = os.environ.get("BOOKING_SERVICE_URL", "http://127.0.0.1:3002/graphql")

DETAILED_BOOKING_QUERY = """
query GetDetailedBooking($userid: String!) {
    detailed_booking_with_id(_userid: $userid) {
        userid
        dates {
            date
            movies {
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
    }
}
"""

with open('{}/data/users.json'.format("."), "r") as jsf:
    users = json.load(jsf)["users"]


def write(users_list):
    with open('{}/data/users.json'.format("."), "w") as f:
        json.dump({"users": users_list}, f, indent=2)


def is_admin():
    return request.headers.get("X-Admin", "").lower() == "true"


@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the User service!</h1>", 200)


@app.route("/json", methods=['GET'])
def get_json():
    if not is_admin():
        return make_response(jsonify({"error": "Admin privileges required"}), 403)
    return make_response(jsonify(users), 200)


@app.route("/user/<userid>", methods=['GET'])
def get_user_byid(userid):
    user_info = next((user for user in users if user.get("id") == userid), None)
    if user_info:
        return make_response(jsonify(user_info), 200)
    return make_response(jsonify({"error": "User ID not found"}), 404)


@app.route("/user/<userid>/bookings", methods=['GET'])
def get_user_with_bookings(userid):
    user_info = next((user for user in users if user.get("id") == userid), None)
    if not user_info:
        return make_response(jsonify({"error": "User ID not found"}), 404)

    try:
        resp = requests.post(
            BOOKING_SERVICE_URL,
            json={"query": DETAILED_BOOKING_QUERY, "variables": {"userid": userid}},
            timeout=5
        )
        if resp.status_code != 200:
            return make_response(jsonify({"error": "Booking service error"}), 503)
        payload = resp.json()
        if payload.get("errors"):
            return make_response(jsonify({"error": "Booking service error"}), 503)
        detailed = payload.get("data", {}).get("detailed_booking_with_id")
        bookings_data = detailed.get("dates", []) if detailed else []
    except (requests.RequestException, ValueError):
        return make_response(jsonify({"error": "Booking service unavailable"}), 503)

    return make_response(jsonify({
        **user_info,
        "bookings": bookings_data
    }), 200)


@app.route("/user/<userid>", methods=['POST'])
def add_user(userid):
    req = request.get_json(silent=True)
    if not req or not req.get("name"):
        return make_response(jsonify({"error": "Invalid payload: 'name' is required"}), 400)

    existing_user = next((user for user in users if user.get("id") == userid), None)
    if existing_user:
        return make_response(jsonify({"error": "User ID already exists"}), 409)

    new_user = {
        "id": userid,
        "name": req["name"],
        "last_active": int(req.get("last_active", 0))
    }
    users.append(new_user)
    write(users)
    return make_response(jsonify({"message": "User added successfully", "user": new_user}), 200)


@app.route("/user/<userid>", methods=['PUT'])
def update_user(userid):
    req = request.get_json(silent=True)
    if not req:
        return make_response(jsonify({"error": "Invalid JSON payload"}), 400)

    existing_user = next((user for user in users if user.get("id") == userid), None)
    if not existing_user:
        return make_response(jsonify({"error": "User ID not found"}), 404)

    if "name" in req:
        existing_user["name"] = req["name"]
    if "last_active" in req:
        existing_user["last_active"] = int(req["last_active"])

    write(users)
    return make_response(jsonify({"message": "User updated successfully", "user": existing_user}), 200)


@app.route("/user/<userid>", methods=['DELETE'])
def delete_user(userid):
    if not is_admin():
        return make_response(jsonify({"error": "Admin privileges required"}), 403)

    user_to_delete = next((user for user in users if user.get("id") == userid), None)
    if user_to_delete:
        users.remove(user_to_delete)
        write(users)
        return make_response(jsonify({"message": "User deleted successfully"}), 200)

    return make_response(jsonify({"error": "User ID not found"}), 404)


if __name__ == "__main__":
    print("Server running in port %s" % PORT)
    app.run(host=HOST, port=PORT)
