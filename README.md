# UniScheduler

Base de la première phase de l'application de gestion d'emplois du temps universitaires : authentification, base SQLite et tableau de bord Bootstrap 5.

## Démarrage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

L'application écoute sur `http://localhost:5000`. Au premier lancement, elle crée les comptes de démonstration suivants :

| Utilisateur | Mot de passe | Rôle |
| --- | --- | --- |
| `admin` | `admin123` | Administrateur |
| `prof_dupont` | `password` | Utilisateur |

> Changez `SECRET_KEY` et les identifiants de démonstration avant tout déploiement en production.
