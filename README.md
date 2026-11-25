# UE-AD-A1-MIXTE

## Architecture

| Service           | Technologie     | Protocole |  Port   |
| :---------------- | :-------------- | :-------- | :-----: |
| **movie**         | Flask + Ariadne | GraphQL   | `3001`  |
| **booking**       | Flask + Ariadne | GraphQL   | `3002`  |
| **schedule**      | Flask           | REST      | `3202`  |
| **user**          | Flask           | REST      | `3203`  |
| **mongo**         | MongoDB 7       | —         | `27017` |
| **mongo-express** | Mongo Express 1 | Web UI    | `8081`  |

### Communications inter-services

- **`booking` → `movie`** (GraphQL) :
  - `create_booking` : vérifie que le film existe avant d'enregistrer la réservation.
  - `detailed_booking_with_id` : récupère les détails des films et de leurs acteurs à partir des identifiants stockés.
- **`booking` → `schedule`** (REST) :
  - `create_booking` : vérifie que le film est bien programmé à la date demandée avant d'enregistrer la réservation.

## Structure du projet

```text
.
├── booking/                # Service Booking (GraphQL + MongoDB)
│   ├── booking.graphql
│   ├── booking.py
│   ├── resolvers.py
│   ├── Dockerfile
│   └── data/bookings.json
├── movie/                  # Service Movie (GraphQL + MongoDB)
│   ├── movie.graphql
│   ├── movie.py
│   ├── resolvers.py
│   ├── Dockerfile
│   └── data/
│       ├── movies.json
│       └── actors.json
├── schedule/               # Service Schedule (REST + JSON)
│   ├── schedule.py
│   ├── Dockerfile
│   └── data/times.json
├── user/                   # Service User (REST + JSON)
│   ├── user.py
│   ├── Dockerfile
│   └── data/users.json
├── docker-compose.yml
└── requirements.txt
```

## Démarrage rapide

```bash
docker compose up --build
```

Services disponibles après le démarrage :

- **Movie (GraphQL)** : `http://localhost:3001/graphql`
- **Booking (GraphQL)** : `http://localhost:3002/graphql`
- **Schedule (REST)** : `http://localhost:3202`
- **User (REST)** : `http://localhost:3203`
- **Mongo Express** : `http://localhost:8081`

Pour arrêter les conteneurs :

```bash
docker compose down
```

Pour supprimer également les données persistées dans MongoDB :

```bash
docker compose down -v
```

## Documentation des API

### Service `movie` — GraphQL (`POST http://localhost:3001/graphql`)

Au premier démarrage, si les collections MongoDB `movies.movies` et `movies.actors` sont vides, elles sont automatiquement initialisées à partir de `movie/data/movies.json` et `movie/data/actors.json`.

| Type       | Opération                                                                                | Description                                             |
| :--------- | :--------------------------------------------------------------------------------------- | :------------------------------------------------------ |
| `Query`    | `all_movies: [Movie!]!`                                                                  | Liste tous les films                                    |
| `Query`    | `movie_with_id(_id: String!): Movie`                                                     | Récupère un film par son identifiant (avec ses acteurs) |
| `Query`    | `all_actors: [Actor!]!`                                                                  | Liste tous les acteurs                                  |
| `Query`    | `actors_with_id(_id: String!): Actor`                                                    | Récupère un acteur par son identifiant                  |
| `Mutation` | `create_movie(_title: String!, _director: String!, _rating: Float!, _id: String): Movie` | Crée un film (`_id` généré automatiquement si omis)     |
| `Mutation` | `update_movie(_id: String!, _title: String, _director: String, _rating: Float): Movie`   | Met à jour les champs fournis d'un film                 |
| `Mutation` | `update_movie_rate(_id: String!, _rate: Float!): Movie`                                  | Met à jour la note d'un film                            |
| `Mutation` | `delete_movie(_id: String!): Boolean!`                                                   | Supprime un film par son identifiant                    |

Exemple de requête :

```graphql
query {
  all_movies {
    id
    title
    director
    rating
    actors {
      firstname
      lastname
    }
  }
}
```

### Service `booking` — GraphQL (`POST http://localhost:3002/graphql`)

Au premier démarrage, si la collection MongoDB `booking.bookings` est vide, elle est automatiquement initialisée à partir de `booking/data/bookings.json`.

| Type       | Opération                                                                       | Description                                                                                    |
| :--------- | :------------------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------- |
| `Query`    | `all_bookings: [Booking!]!`                                                     | Liste toutes les réservations                                                                  |
| `Query`    | `booking_with_id(_userid: String!): Booking`                                    | Récupère les réservations d'un utilisateur                                                     |
| `Query`    | `detailed_booking_with_id(_userid: String!): DetailedBooking`                   | Récupère les réservations d'un utilisateur avec les détails des films et acteurs (via `movie`) |
| `Mutation` | `create_booking(_userid: String!, _date: String!, _movie_id: String!): Booking` | Ajoute une réservation après vérification dans `schedule` et `movie`                           |
| `Mutation` | `delete_booking(_userid: String!): Boolean!`                                    | Supprime les réservations d'un utilisateur                                                     |

Exemple de mutation :

```graphql
mutation {
  create_booking(
    _userid: "chris_rivers"
    _date: "20151130"
    _movie_id: "720d006c-3a57-4b6a-b18f-9b713b073f3c"
  ) {
    userid
    dates {
      date
      movies
    }
  }
}
```

### Service `schedule` — REST (`http://localhost:3202`)

| Méthode  | Endpoint              | Description                                       |
| :------- | :-------------------- | :------------------------------------------------ |
| `GET`    | `/`                   | Message d'accueil                                 |
| `GET`    | `/json`               | Liste complète des programmations                 |
| `GET`    | `/schedule/<movieid>` | Dates de projection pour un film                  |
| `POST`   | `/schedule/<movieid>` | Ajoute une programmation (`{"date": "YYYYMMDD"}`) |
| `PUT`    | `/schedule/<movieid>` | Met à jour la date de projection d'un film        |
| `DELETE` | `/schedule/<movieid>` | Supprime une programmation pour un film           |

### Service `user` — REST (`http://localhost:3203`)

| Méthode  | Endpoint         | Description                                 |
| :------- | :--------------- | :------------------------------------------ |
| `GET`    | `/`              | Message d'accueil                           |
| `GET`    | `/json`          | Liste complète des utilisateurs             |
| `GET`    | `/user/<userid>` | Récupère un utilisateur par son identifiant |
| `POST`   | `/user/<userid>` | Crée ou met à jour un utilisateur           |
| `PUT`    | `/user/<userid>` | Met à jour un utilisateur existant          |
| `DELETE` | `/user/<userid>` | Supprime un utilisateur                     |

## Licence

Ce projet est distribué sous licence GNU GPL v3. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
