# Scénario Bruno — La sortie ciné d'Alice

## Fil rouge

**Alice Martin** souhaite aller voir **Interstellar** au cinéma :

1. On s'assure d'abord que les 4 microservices répondent (**Statut**).
2. **Alice** crée son compte utilisateur (**User**).
3. Le cinéma (avec le header `X-Admin: true`) ajoute **Interstellar** au catalogue, met à jour sa note suite aux critiques et vérifie sa fiche (**Movie**).
4. Le cinéma (avec le header `X-Admin: true`) programme une séance pour **Interstellar** le `20261201`, vérifie la séance et consulte la programmation détaillée enrichie avec les détails du film (**Schedule**).
5. **Alice** tente d'abord de réserver le `20261205` (refusé car aucune séance ce jour-là), puis réserve sur la bonne date (`20261201`), consulte son récapitulatif détaillé (**Booking** → **Movie**), vérifie que `all_bookings` est protégé par `X-Admin: true`, et consulte enfin son profil utilisateur enrichi de ses réservations (**User** → **Booking** → **Movie**).

---

## Prérequis

Démarrer les services depuis la racine du projet :

```bash
docker compose up --build
```

| Service      | Protocole | URL                             |
| :----------- | :-------- | :------------------------------ |
| **User**     | REST      | `http://localhost:3203`         |
| **Movie**    | GraphQL   | `http://localhost:3001/graphql` |
| **Schedule** | REST      | `http://localhost:3202`         |
| **Booking**  | GraphQL   | `http://localhost:3002/graphql` |

---

## Étapes du scénario

### 01 — Statut des services

|  #  | Requête                        | Appel        | Résultat attendu           |
| :-: | :----------------------------- | :----------- | :------------------------- |
|  1  | **Statut du service User**     | `GET :3203/` | `200` — Service disponible |
|  2  | **Statut du service Movie**    | `GET :3001/` | `200` — Service disponible |
|  3  | **Statut du service Schedule** | `GET :3202/` | `200` — Service disponible |
|  4  | **Statut du service Booking**  | `GET :3002/` | `200` — Service disponible |

### 02 — User

|  #  | Requête                        | Appel                     | Rôle dans le fil rouge                             |
| :-: | :----------------------------- | :------------------------ | :------------------------------------------------- |
|  1  | **Créer le compte d'Alice**    | `POST /user/alice_martin` | Alice s'inscrit sur l'application                  |
|  2  | **Vérifier le compte d'Alice** | `GET /user/alice_martin`  | Confirme que le profil d'Alice est bien enregistré |

### 03 — Movie

|  #  | Requête                                  | Opération GraphQL            | Header          | Rôle dans le fil rouge                                                               |
| :-: | :--------------------------------------- | :--------------------------- | :-------------- | :----------------------------------------------------------------------------------- |
|  1  | **Ajouter le film Interstellar**         | `mutation create_movie`      | `X-Admin: true` | Le cinéma ajoute _Interstellar_ (`f47ac10b-58cc-4372-a567-0e02b2c3d479`, note `8.6`) |
|  2  | **Mettre à jour la note d'Interstellar** | `mutation update_movie_rate` | `X-Admin: true` | La note du film passe à `9.0`                                                        |
|  3  | **Consulter la fiche d'Interstellar**    | `query movie_with_id`        | —               | Vérifie la fiche à jour avant programmation                                          |

### 04 — Schedule

|  #  | Requête                                           | Appel                                | Header          | Rôle dans le fil rouge                                                                   |
| :-: | :------------------------------------------------ | :----------------------------------- | :-------------- | :--------------------------------------------------------------------------------------- |
|  1  | **Programmer une séance d'Interstellar**          | `POST /schedule/f47ac10b-...`        | `X-Admin: true` | Le cinéma programme la séance le `20261201` (après vérif `schedule` → `movie`)           |
|  2  | **Vérifier les séances d'Interstellar**           | `GET /schedule/f47ac10b-...`         | —               | Confirme que `20261201` apparaît dans la programmation                                   |
|  3  | **Consulter la programmation détaillée 20261201** | `GET /schedule/date/20261201/details` | —               | Retourne la séance enrichie avec les détails d'_Interstellar_ via `schedule` → `movie`   |

### 05 — Booking & Recoupements

|  #  | Requête                                           | Appel / Opération                | Header          | Rôle dans le fil rouge                                                                                    |
| :-: | :------------------------------------------------ | :------------------------------- | :-------------- | :-------------------------------------------------------------------------------------------------------- |
|  1  | **Tenter une réservation sur une mauvaise date**  | `mutation create_booking`        | —               | Alice essaie le `20261205` → refusé (`null`), démontre la vérification `booking` → `schedule`             |
|  2  | **Réserver Interstellar pour Alice**              | `mutation create_booking`        | —               | Alice réserve le `20261201` → validé après appels `booking` → `user`, `schedule` et `movie`               |
|  3  | **Consulter la réservation détaillée d'Alice**    | `query detailed_booking_with_id` | —               | Retourne la réservation enrichie avec titre, réalisateur et note (`9.0`) via `booking` → `movie`          |
|  4  | **Refuser `all_bookings` sans privilèges admin**  | `query all_bookings`             | —               | Retourne une erreur GraphQL `Admin privileges required`                                                   |
|  5  | **Lister toutes les réservations (Admin)**        | `query all_bookings`             | `X-Admin: true` | Retourne toutes les réservations, dont celle d'Alice                                                      |
|  6  | **Consulter le profil d'Alice avec réservations** | `GET /user/alice_martin/bookings` | —               | Retourne le profil d'Alice enrichi de ses réservations détaillées via `user` → `booking` → `movie`        |

---
