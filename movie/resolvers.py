import json
import uuid

def movie_with_id(_, info, _id):
    with open('{}/data/movies.json'.format("."), "r") as file:
        movies = json.load(file)
        for movie in movies.get('movies', []):
            if movie['id'] == _id:
                return movie
    return None

def all_movies(_, info):
    with open('{}/data/movies.json'.format("."), "r") as file:
        movies = json.load(file)
        return movies.get('movies', [])

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
    with open('{}/data/movies.json'.format("."), "r") as rfile:
        data = json.load(rfile)
    movie_id = _id if _id else str(uuid.uuid4())
    new_movie = {
        "id": movie_id,
        "title": _title,
        "director": _director,
        "rating": _rating
    }
    data.setdefault("movies", []).append(new_movie)
    with open('{}/data/movies.json'.format("."), "w") as wfile:
        json.dump(data, wfile, indent=2)
    return new_movie

def update_movie_rate(_, info, _id, _rate):
    with open('{}/data/movies.json'.format("."), "r") as rfile:
        data = json.load(rfile)
    target = None
    for movie in data.get('movies', []):
        if movie['id'] == _id:
            movie['rating'] = _rate
            target = movie
            break
    if target:
        with open('{}/data/movies.json'.format("."), "w") as wfile:
            json.dump(data, wfile, indent=2)
    return target

def update_movie(_, info, _id, _title=None, _director=None, _rating=None):
    with open('{}/data/movies.json'.format("."), "r") as rfile:
        data = json.load(rfile)
    target = None
    for movie in data.get('movies', []):
        if movie['id'] == _id:
            if _title is not None:
                movie['title'] = _title
            if _director is not None:
                movie['director'] = _director
            if _rating is not None:
                movie['rating'] = _rating
            target = movie
            break
    if target:
        with open('{}/data/movies.json'.format("."), "w") as wfile:
            json.dump(data, wfile, indent=2)
    return target

def delete_movie(_, info, _id):
    with open('{}/data/movies.json'.format("."), "r") as rfile:
        data = json.load(rfile)
    movies = data.get('movies', [])
    total_before = len(movies)
    data['movies'] = [m for m in movies if m['id'] != _id]
    if len(data['movies']) < total_before:
        with open('{}/data/movies.json'.format("."), "w") as wfile:
            json.dump(data, wfile, indent=2)
        return True
    return False

def resolve_actors_in_movie(movie, info):
    with open('{}/data/actors.json'.format("."), "r") as file:
        actors = json.load(file)
        result = [actor for actor in actors.get('actors', []) if movie['id'] in actor.get('films', [])]
        return result
