# UE-AD-A1-MIXTE

## Architecture

| Service           | Technologie     | Protocole |  Port   | Documentation OpenAPI                                 |
| :---------------- | :-------------- | :-------- | :-----: | :---------------------------------------------------- |
| **movie**         | Flask + Ariadne | GraphQL   | `3001`  | [movie/movie.yaml](movie/movie.yaml)                  |
| **booking**       | Flask + Ariadne | GraphQL   | `3002`  | [booking/booking.yaml](booking/booking.yaml)          |
| **schedule**      | Flask           | REST      | `3202`  | [schedule/schedule.yaml](schedule/schedule.yaml)      |
| **user**          | Flask           | REST      | `3203`  | [user/user.yaml](user/user.yaml)                      |
| **mongo**         | MongoDB 7       | —         | `27017` | —                                                     |
| **mongo-express** | Mongo Express 1 | Web UI    | `8081`  | —                                                     |

### Communications inter-services

- **`booking` → `movie`** (GraphQL) :
  - `create_booking` : vérifie que le film existe avant d'enregistrer la réservation.
  - `detailed_booking_with_id` : récupère les détails des films et de leurs acteurs à partir des identifiants stockés.
- **`booking` → `schedule`** (REST) :
  - `create_booking` : vérifie que le film est bien programmé à la date demandée avant d'enregistrer la réservation.
- **`booking` → `user`** (REST) :
  - `create_booking` : vérifie que l'utilisateur existe avant d'enregistrer la réservation.
- **`schedule` → `movie`** (GraphQL) :
  - `POST /schedule/<movieid>` : vérifie que le film existe avant de programmer une séance.
  - `GET /schedule/date/<date>/details` : enrichit la programmation d'une date avec les détails complets des films.
- **`user` → `booking`** (GraphQL) :
  - `GET /user/<userid>/bookings` : récupère le profil d'un utilisateur enrichi de ses réservations détaillées.

### Contrôle d'accès (`X-Admin`)

Les opérations d'administration nécessitent le header HTTP `X-Admin: true` :
- **Movie (GraphQL)** : `create_movie`, `update_movie`, `update_movie_rate`, `delete_movie`.
- **Booking (GraphQL)** : `all_bookings`.
- **Schedule (REST)** : `POST /schedule/<movieid>`, `DELETE /schedule/<movieid>`.
- **User (REST)** : `GET /json`, `DELETE /user/<userid>`.

## Structure du projet

```text
.
├── booking/                # Service Booking (GraphQL + MongoDB)
│   ├── booking.graphql
│   ├── booking.py
│   ├── resolvers.py
│   ├── booking.yaml
│   ├── Dockerfile
│   └── data/bookings.json
├── movie/                  # Service Movie (GraphQL + MongoDB)
│   ├── movie.graphql
│   ├── movie.py
│   ├── resolvers.py
│   ├── movie.yaml
│   ├── Dockerfile
│   └── data/
│       ├── movies.json
│       └── actors.json
├── schedule/               # Service Schedule (REST + JSON)
│   ├── schedule.py
│   ├── schedule.yaml
│   ├── Dockerfile
│   └── data/times.json
├── user/                   # Service User (REST + JSON)
│   ├── user.py
│   ├── user.yaml
│   ├── Dockerfile
│   └── data/users.json
├── bruno/                  # Scénario et requêtes de test Bruno
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

Des spécifications OpenAPI 3.0 complètes (avec descriptions des entrées/sorties et exemples) sont disponibles dans `movie/movie.yaml`, `booking/booking.yaml`, `schedule/schedule.yaml` et `user/user.yaml`.

### Service `movie` — GraphQL (`POST http://localhost:3001/graphql`)

Au premier démarrage, si les collections MongoDB `movies.movies` et `movies.actors` sont vides, elles sont automatiquement initialisées à partir de `movie/data/movies.json` et `movie/data/actors.json`.

| Type       | Opération                                                                                | Admin | Description                                             |
| :--------- | :--------------------------------------------------------------------------------------- | :---: | :------------------------------------------------------ |
| `Query`    | `all_movies: [Movie!]!`                                                                  |  Non  | Liste tous les films                                    |
| `Query`    | `movie_with_id(_id: String!): Movie`                                                     |  Non  | Récupère un film par son identifiant (avec ses acteurs) |
| `Query`    | `all_actors: [Actor!]!`                                                                  |  Non  | Liste tous les acteurs                                  |
| `Query`    | `actors_with_id(_id: String!): Actor`                                                    |  Non  | Récupère un acteur par son identifiant                  |
| `Mutation` | `create_movie(_title: String!, _director: String!, _rating: Float!, _id: String): Movie` |  Oui  | Crée un film (`_id` généré automatiquement si omis)     |
| `Mutation` | `update_movie(_id: String!, _title: String, _director: String, _rating: Float): Movie`   |  Oui  | Met à jour les champs fournis d'un film                 |
| `Mutation` | `update_movie_rate(_id: String!, _rate: Float!): Movie`                                  |  Oui  | Met à jour la note d'un film                            |
| `Mutation` | `delete_movie(_id: String!): Boolean!`                                                   |  Oui  | Supprime un film par son identifiant                    |

### Service `booking` — GraphQL (`POST http://localhost:3002/graphql`)

Au premier démarrage, si la collection MongoDB `booking.bookings` est vide, elle est automatiquement initialisée à partir de `booking/data/bookings.json`.

| Type       | Opération                                                                       | Admin | Description                                                                                    |
| :--------- | :------------------------------------------------------------------------------ | :---: | :--------------------------------------------------------------------------------------------- |
| `Query`    | `all_bookings: [Booking!]!`                                                     |  Oui  | Liste toutes les réservations                                                                  |
| `Query`    | `booking_with_id(_userid: String!): Booking`                                    |  Non  | Récupère les réservations d'un utilisateur                                                     |
| `Query`    | `detailed_booking_with_id(_userid: String!): DetailedBooking`                   |  Non  | Récupère les réservations d'un utilisateur avec les détails des films et acteurs (via `movie`) |
| `Mutation` | `create_booking(_userid: String!, _date: String!, _movie_id: String!): Booking` |  Non  | Ajoute une réservation après vérification dans `user`, `schedule` et `movie`                   |
| `Mutation` | `delete_booking(_userid: String!): Boolean!`                                    |  Non  | Supprime les réservations d'un utilisateur                                                     |

### Service `schedule` — REST (`http://localhost:3202`)

| Méthode  | Endpoint                        | Admin | Description                                                          |
| :------- | :------------------------------ | :---: | :------------------------------------------------------------------- |
| `GET`    | `/`                             |  Non  | Message d'accueil                                                    |
| `GET`    | `/json`                         |  Non  | Liste complète des programmations                                    |
| `GET`    | `/schedule/<movieid>`           |  Non  | Dates de projection pour un film                                     |
| `GET`    | `/schedule/date/<date>`         |  Non  | Identifiants des films programmés à une date                         |
| `GET`    | `/schedule/date/<date>/details` |  Non  | Programmation d'une date enrichie avec les détails des films (`movie`) |
| `POST`   | `/schedule/<movieid>`           |  Oui  | Ajoute une programmation (`{"date": "YYYYMMDD"}`) après vérif `movie` |
| `DELETE` | `/schedule/<movieid>`           |  Oui  | Supprime un film d'une date (`?date=YYYYMMDD`) ou de toutes les dates |

### Service `user` — REST (`http://localhost:3203`)

| Méthode  | Endpoint                  | Admin | Description                                                                    |
| :------- | :------------------------ | :---: | :----------------------------------------------------------------------------- |
| `GET`    | `/`                       |  Non  | Message d'accueil                                                              |
| `GET`    | `/json`                   |  Oui  | Liste complète des utilisateurs                                                |
| `GET`    | `/user/<userid>`          |  Non  | Récupère un utilisateur par son identifiant                                    |
| `GET`    | `/user/<userid>/bookings` |  Non  | Récupère un utilisateur enrichi de ses réservations détaillées (`booking`)     |
| `POST`   | `/user/<userid>`          |  Non  | Crée un nouvel utilisateur                                                     |
| `PUT`    | `/user/<userid>`          |  Non  | Met à jour un utilisateur existant                                             |
| `DELETE` | `/user/<userid>`          |  Oui  | Supprime un utilisateur                                                        |

## Licence

Ce projet est distribué sous licence GNU GPL v3. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
