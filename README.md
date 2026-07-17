# Scheduler Maker

Scheduler Maker est une application Flask légère pour générer des emplois du temps universitaires en respectant les affectations pédagogiques déjà décidées par la faculté.

## Périmètre fonctionnel

- L'administrateur encode les professeurs, leurs jours d'indisponibilité, les salles et les cours.
- Chaque cours contient son professeur déjà affecté, ses crédits, son volume horaire, ses promotions, ses départements et son semestre.
- Le moteur génère les créneaux sans attribuer de cours aux professeurs à la place de la faculté.
- La génération empêche les conflits suivants : professeur occupé deux fois, salle occupée deux fois, ou même promotion/département programmé sur deux cours au même créneau.
- Le résultat est consultable dans l'interface HTML et imprimable.

## Organisation du code

- `app.py` contient l'application Flask, les routes web et le raccordement avec SQLite.
- `scheduler.py` contient le modèle SQLite et l'algorithme de génération testable sans dépendre de Flask.
- `templates/` contient les pages Jinja2 de saisie et de résultat.
- `static/css/style.css` contient la mise en page responsive et les styles d'impression.
- `tests/test_scheduler.py` vérifie le moteur de génération avec une base SQLite en mémoire.

## Modèle de données

L'application utilise SQLite via la bibliothèque standard Python :

- `professors(id, name, email, unavailable_days)`
- `rooms(id, name, capacity)`
- `courses(id, name, credits, total_hours, professor_id, cohorts, departments, semester)`
- `schedule_entries(id, course_id, professor_id, room_id, day, start_time, end_time)`

## Démarrage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run
```

Ouvrez ensuite <http://127.0.0.1:5000>.

## Validation rapide

```bash
python -m compileall app.py scheduler.py tests/test_scheduler.py
python -m unittest discover -s tests -v
```
