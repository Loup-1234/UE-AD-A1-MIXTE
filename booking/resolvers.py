import json

DATA_PATH = "./data/bookings.json"

def _read_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def booking_with_id(_, info, _userid):
    data = _read_data()
    for booking in data.get("bookings", []):
        if booking["userid"] == _userid:
            return booking
    return None

def update_booking_date(_, info, _userid, _movie_id, _date):
    donnees = _read_data()
    reservations = donnees.get("bookings", [])

    # Trouver l'utilisateur
    utilisateur = next(
        (resa for resa in reservations if resa["userid"] == _userid), None
    )
    if not utilisateur:
        return None

    # 1. Retirer le film de son ancienne date
    for planning in utilisateur.get("dates", []):
        if _movie_id in planning["movies"]:
            planning["movies"].remove(_movie_id)

    # 2. Trouver la date cible ou la créer
    planning_cible = next(
        (p for p in utilisateur["dates"] if p["date"] == _date), None
    )
    if not planning_cible:
        planning_cible = {"date": _date, "movies": []}
        utilisateur["dates"].append(planning_cible)

    # 3. Ajouter le film à la nouvelle date
    if _movie_id not in planning_cible["movies"]:
        planning_cible["movies"].append(_movie_id)

    _write_data(donnees)
    return utilisateur


def delete_booking(_, info, _userid):
    donnees = _read_data()
    reservations = donnees.get("bookings", [])

    total_avant = len(reservations)
    donnees["bookings"] = [
        resa for resa in reservations if resa["userid"] != _userid
    ]

    # Sauvegarde uniquement si un utilisateur a bien été supprimé
    if len(donnees["bookings"]) < total_avant:
        _write_data(donnees)
        return True

    return False

def delete_booking_date(_, info, _userid, _date):
    data = _read_data()
    target_booking = None

    for booking in data.get("bookings", []):
        if booking["userid"] == _userid:
            booking["dates"] = [d for d in booking.get("dates", []) if d["date"] != _date]
            target_booking = booking
            break

    if target_booking:
        _write_data(data)

    return target_booking