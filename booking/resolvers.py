import json
import os
import requests
from graphql import GraphQLError
from pymongo import MongoClient

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://root:example@localhost:27017/"
)
MOVIE_SERVICE_URL = os.getenv(
    "MOVIE_SERVICE_URL",
    "http://127.0.0.1:3001/graphql"
)
SCHEDULE_SERVICE_URL = os.getenv(
    "SCHEDULE_SERVICE_URL",
    "http://127.0.0.1:3202"
)
USER_SERVICE_URL = os.getenv(
    "USER_SERVICE_URL",
    "http://127.0.0.1:3203"
)

client = MongoClient(MONGO_URI)

db = client["booking"]
collection = db["bookings"]

with open("./data/bookings.json", "r") as file:
    data = json.load(file)
    bookings = data.get("bookings", [])

if collection.count_documents({}) == 0 and bookings:
    collection.insert_many(bookings)
    print("Réservations insérées dans MongoDB !")

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


def is_admin(info):
    req = (info.context or {}).get("request")
    if not req:
        return False
    return req.headers.get("X-Admin", "").lower() == "true"


def booking_with_id(_, info, _userid):
    return collection.find_one({"userid": _userid})


def all_bookings(_, info):
    if not is_admin(info):
        raise GraphQLError("Admin privileges required")
    return list(collection.find())


def detailed_booking_with_id(_, info, _userid):
    booking = collection.find_one({"userid": _userid})
    if not booking:
        return None

    detailed_dates = []
    for date_entry in booking.get("dates", []):
        movies = [get_movie(movie_id) for movie_id in date_entry.get("movies", [])]
        detailed_dates.append({
            "date": date_entry.get("date"),
            "movies": [movie for movie in movies if movie]
        })

    return {
        "userid": booking["userid"],
        "dates": detailed_dates
    }


def create_booking(_, info, _userid, _date, _movie_id):
    if not user_exists(_userid) or not is_scheduled(_movie_id, _date) or not get_movie(_movie_id):
        return None

    result = collection.update_one(
        {"userid": _userid, "dates.date": _date},
        {"$addToSet": {"dates.$.movies": _movie_id}}
    )

    if result.matched_count == 0:
        new_date = {
            "date": _date,
            "movies": [_movie_id]
        }
        collection.update_one(
            {"userid": _userid},
            {"$push": {"dates": new_date}},
            upsert=True
        )

    return collection.find_one({"userid": _userid})


def delete_booking(_, info, _userid):
    result = collection.delete_one({"userid": _userid})
    return result.deleted_count > 0


def user_exists(userid):
    try:
        response = requests.get(
            f"{USER_SERVICE_URL}/user/{userid}",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def get_movie(movie_id):
    try:
        response = requests.post(
            MOVIE_SERVICE_URL,
            json={"query": MOVIE_QUERY, "variables": {"id": movie_id}},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("data", {}).get("movie_with_id")
    except Exception:
        pass
    return None


def is_scheduled(movie_id, date):
    try:
        response = requests.get(
            f"{SCHEDULE_SERVICE_URL}/schedule/{movie_id}",
            timeout=5
        )
        dates = response.json() if response.status_code == 200 else []
        return isinstance(dates, list) and date in dates
    except Exception:
        return False
