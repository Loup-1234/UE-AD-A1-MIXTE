import json
import os
import requests

MOVIE_SERVICE_URL = os.environ.get("MOVIE_SERVICE_URL", "http://127.0.0.1:3001/graphql")
SCHEDULE_SERVICE_URL = os.environ.get("SCHEDULE_SERVICE_URL", "http://127.0.0.1:3202")

def _read_data():
    with open('{}/data/bookings.json'.format("."), "r") as file:
        return json.load(file)

def _write_data(data):
    with open('{}/data/bookings.json'.format("."), "w") as file:
        json.dump(data, file, indent=2)

def booking_with_id(_, info, _userid):
    bookings = _read_data()
    for booking in bookings.get('bookings', []):
        if booking['userid'] == _userid:
            return booking
    return None

def all_bookings(_, info):
    bookings = _read_data()
    return bookings.get('bookings', [])

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
    bookings = _read_data()
    for booking in bookings.get('bookings', []):
        if booking['userid'] == _userid:
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

    bookings = _read_data()
    user_booking = next((b for b in bookings.get('bookings', []) if b['userid'] == _userid), None)

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
        bookings.setdefault('bookings', []).append(user_booking)
    else:
        date_entry = next((d for d in user_booking.get('dates', []) if d['date'] == _date), None)
        if date_entry:
            if _movie_id not in date_entry['movies']:
                date_entry['movies'].append(_movie_id)
        else:
            user_booking.setdefault('dates', []).append({
                "date": _date,
                "movies": [_movie_id]
            })

    _write_data(bookings)
    return user_booking

def delete_booking(_, info, _userid):
    bookings = _read_data()
    all_bookings = bookings.get('bookings', [])
    total_before = len(all_bookings)
    bookings['bookings'] = [b for b in all_bookings if b['userid'] != _userid]

    if len(bookings['bookings']) < total_before:
        _write_data(bookings)
        return True
    return False
