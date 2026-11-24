import json
import uuid
import os
from pymongo import MongoClient

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://root:example@localhost:27017/"
)

client = MongoClient(MONGO_URI)

db = client["movies"]
collection = db["movies"]
with open("./data/movies.json", "r") as file:
    data = json.load(file)
    movies = data.get("movies", [])

if collection.count_documents({}) == 0 and movies:
    collection.insert_many(movies)
    print("Films insérés dans MongoDB !")

def movie_with_id(_, info, _id):
    return collection.find_one({"id": _id})

def all_movies(_, info):
    return list(collection.find())
    
def actors_with_id(_, info, _id):
    with open('{}/data/actors.json'.format("."), "r") as file:
        actors = json.load(file)
        for actor in actors.get('actors', []):
            if actor['id'] == _id:
                return actor
    return None

def all_actors(_, info):
    with open('{}/data/actors.json'.format("."), "r") as file:
        actors = json.load(file)
        return actors.get('actors', [])

def create_movie(_, info, _title, _director, _rating, _id=None):
    movie_id = _id if _id else str(uuid.uuid4())

    new_movie = {
        "id": movie_id,
        "title": _title,
        "director": _director,
        "rating": _rating
    }

    collection.insert_one(new_movie)

    return new_movie

def update_movie_rate(_, info, _id, _rate):
    collection.update_one(
        {"id": _id},
        {"$set": {"rating": float(_rate)}}
    )

    return collection.find_one({"id": _id})

def update_movie(_, info, _id, _title=None, _director=None, _rating=None):
    newvalues = {}

    if _title is not None:
        newvalues["title"] = _title

    if _director is not None:
        newvalues["director"] = _director

    if _rating is not None:
        newvalues["rating"] = float(_rating)

    if newvalues:
        collection.update_one(
            {"id": _id},
            {"$set": newvalues}
        )

    return collection.find_one({"id": _id})

def delete_movie(_, info, _id):
    result = collection.delete_one({"id": _id})
    return result.deleted_count > 0

def resolve_actors_in_movie(movie, info):
    with open('{}/data/actors.json'.format("."), "r") as file:
        actors = json.load(file)
        result = [actor for actor in actors.get('actors', []) if movie['id'] in actor.get('films', [])]
        return result
