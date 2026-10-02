import json

def booking_with_id(_, info, _userid):
    with open('{}/data/bookings.json'.format("."), "r") as file:
        bookings = json.load(file)
        for booking in bookings['bookings']:
            if booking['userid'] == _userid:
                return booking

def update_booking_date(_, info, _userid, _date):
    newbookings = {}
    newbooking = {}
    with open('{}/data/bookings.json'.format("."), "r") as rfile:
        bookings = json.load(rfile)
        for booking in bookings['bookings']:
            if booking['userid'] == _userid:
                booking['date'] = _date
                newbooking = booking
                newbookings = bookings
    with open('{}/data/bookings.json'.format("."), "w") as wfile:
        json.dump(newbookings, wfile)
    return newbooking