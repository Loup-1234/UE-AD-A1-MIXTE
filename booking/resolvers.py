import json
import os
import requests
from pymongo import MongoClient

MOVIE_SERVICE_URL = os.environ.get("MOVIE_SERVICE_URL", "http://127.0.0.1:3001/graphql")
SCHEDULE_SERVICE_URL = os.environ.get("SCHEDULE_SERVICE_URL", "http://127.0.0.1:3202")
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://root:example@localhost:27017/"
)

client = MongoClient(MONGO_URI)

db = client["booking"]
collection = db["bookings"]



def booking_with_id(_, info, _userid):
    return collection.find_one({"userid": _userid})

def all_bookings(_, info):
    return list(collection.find())

def _get_movie_details(movie_id):
    query = """
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
    try:
        response = requests.post(
            MOVIE_SERVICE_URL,
            json={"query": query, "variables": {"id": movie_id}},
            timeout=5
        )
        if response.status_code == 200:
            res_json = response.json()
            return res_json.get("data", {}).get("movie_with_id")
    except Exception:
        pass
    return None

def detailed_booking_with_id(_, info, _userid):
    booking = collection.find_one({"userid": _userid})
    if booking:
        detailed_dates = []
        for d in booking.get('dates', []):
            movies_details = []
            for movie_id in d.get('movies', []):
                movie_detail = _get_movie_details(movie_id)
                if movie_detail:
                    movies_details.append(movie_detail)
            detailed_dates.append({
                "date": d.get("date"),
                "movies": movies_details
            })
        return {
            "userid": booking["userid"],
            "dates": detailed_dates
        }
    return None

def create_booking(_, info, _userid, _date, _movie_id):
    try:
        sched_resp = requests.get(f"{SCHEDULE_SERVICE_URL}/schedule/{_movie_id}", timeout=5)
        if sched_resp.status_code != 200:
            return None
        dates = sched_resp.json()
        if not isinstance(dates, list) or _date not in dates:
            return None
    except Exception:
        return None

    movie_query = """
    query CheckMovie($id: String!) {
        movie_with_id(_id: $id) {
            id
        }
    }
    """
    try:
        movie_resp = requests.post(
            MOVIE_SERVICE_URL,
            json={"query": movie_query, "variables": {"id": _movie_id}},
            timeout=5
        )
        if movie_resp.status_code != 200:
            return None
        movie_data = movie_resp.json().get("data", {}).get("movie_with_id")
        if not movie_data:
            return None
    except Exception:
        return None

    
    user_booking = collection.find_one({"userid": _userid})

    if not user_booking:
        user_booking = {
            "userid": _userid,
            "dates": [
                {
                    "date": _date,
                    "movies": [_movie_id]
                }
            ]
        }
        collection.insert_one(user_booking)

    else:
        date_entry = next(
            (d for d in user_booking.get("dates", []) if d["date"] == _date),
            None
        )

        if date_entry:
            if _movie_id not in date_entry["movies"]:
                collection.update_one(
                    {"userid": _userid, "dates.date": _date},
                    {"$addToSet": {"dates.$.movies": _movie_id}}
                )
        else:
            collection.update_one(
                {"userid": _userid},
                {"$push": {
                    "dates": {
                        "date": _date,
                        "movies": [_movie_id]
                    }
                }}
            )

    return collection.find_one({"userid": _userid})



def delete_booking(_, info, _userid):
    result = collection.delete_one({"userid": _userid})
    return result.deleted_count > 0
