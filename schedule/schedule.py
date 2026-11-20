from flask import Flask, render_template, request, jsonify, make_response
import json
from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3202
HOST = '0.0.0.0'

with open('{}/data/times.json'.format("."), "r") as jsf:
   schedule = json.load(jsf)["schedule"]
   print(schedule)

def write(schedule):
   with open('{}/data/times.json'.format("."), "w") as f:
      full = {}
      full['schedule'] = schedule
      json.dump(full, f)

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"

@app.route("/json", methods=['GET'])
def get_json():
   return make_response(jsonify(schedule),200)

@app.route("/schedule/<movieid>", methods=['GET'])
def get_schedule_byid(movieid):
   movie_dates = [
      showtime["date"] for showtime in schedule
      if movieid in showtime["movies"]
   ]

   if movie_dates:
      return make_response(jsonify(movie_dates),200)

   return make_response(jsonify({"error":"Movie ID not found"}),404)

@app.route("/schedule/<movieid>", methods=['POST'])
def add_schedule(movieid):
   req = request.get_json()
   new_schedule = {
      "date": req.get("date"),
      "movies": [movieid]
   }
   schedule.append(new_schedule)

   write(schedule)

   return make_response(jsonify({"message":"Schedule added successfully"}),200)

@app.route("/schedule/<movieid>", methods=['PUT'])
def update_schedule(movieid):
   req = request.get_json()
   for showtime in schedule:
      if movieid in showtime["movies"]:
         showtime["date"] = req.get("date", showtime["date"])
         write(schedule)
         return make_response(jsonify({"message":"Schedule updated successfully"}),200)
   
   return make_response(jsonify({"error":"Movie ID not found"}),404)

@app.route("/schedule/<movieid>", methods=['DELETE'])
def delete_schedule(movieid):
   for showtime in schedule:
      if movieid in showtime["movies"]:
         schedule.remove(showtime)
         write(schedule)
         return make_response(jsonify({"message":"Schedule deleted successfully"}),200)
   
   return make_response(jsonify({"error":"Movie ID not found"}),404)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
