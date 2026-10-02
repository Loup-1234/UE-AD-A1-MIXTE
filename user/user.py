from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3203
HOST = '0.0.0.0'

with open('{}/databases/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]
   print(users)

def write(users):
   with open('{}/databases/users.json'.format("."), "w") as f:
      full = {}
      full['users'] = users
      json.dump(full, f)

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the User service!</h1>"

@app.route("/json", methods=['GET'])
def get_json():
   return make_response(jsonify(users),200)

@app.route("/user/<userid>", methods=['GET'])
def get_user_byid(userid):
   user_info = next((user for user in users if user.get("userid") == userid), None)

   if user_info:
      return make_response(jsonify(user_info),200)

   return make_response(jsonify({"error":"User ID not found"}),404)

@app.route("/user/<userid>", methods=['POST'])
def add_user(userid):
   req = request.get_json()

   existing_user = next((user for user in users if user.get("userid") == userid), None)

   if existing_user:
      existing_user.update(req)
   else:
      new_user = {
         "userid": userid,
         **req
      }
      users.append(new_user)

   write(users)

   return make_response(jsonify({"message":"User added/updated successfully"}),200)

@app.route("/user/<userid>", methods=['PUT'])
def update_user(userid):
   req = request.get_json()

   existing_user = next((user for user in users if user.get("userid") == userid), None)

   if existing_user:
      existing_user.update(req)
      write(users)
      return make_response(jsonify({"message":"User updated successfully"}),200)

   return make_response(jsonify({"error":"User ID not found"}),404)

@app.route("/user/<userid>", methods=['DELETE'])
def delete_user(userid):
   user_to_delete = next((user for user in users if user.get("userid") == userid), None)

   if user_to_delete:
      users.remove(user_to_delete)
      write(users)
      return make_response(jsonify({"message":"User deleted successfully"}),200)

   return make_response(jsonify({"error":"User ID not found"}),404)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
