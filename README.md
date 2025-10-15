# **Spotify Music Analysis**
This repository aims to collect the huge spotify metadata ( 100 million songs ) using their provided Spotify Web API

## **Setup**
## Developer Login (Public Data)
- In order to retreive publicly available data from spotify, you must register as a developer at developer.spotify.com.
- Then you must create an app in the developer profile, therefore spotify will provide you with client key and client secret.
- Use these in the .env to provide access token to the system.
## User Login (Personal Data)
- In order to retrieve your personal data from spotify, you'll have to login using your spotify account.
- The system will do the rest and gather all your data from Spotify Web API


## Headless mode
Run without a GUI using the CLI entrypoint in `src/Main/headless_main.py`.

Prereqs:
- PostgreSQL reachable per `src/DataBase/database.ini` (see sample `database_ex.ini`).
- Spotify credentials in `config/.env.example` (or change to your real .env path in `spotifyClient.py`).

Examples:
- Fetch Global Top 100, store in DB, then process derived data (songs, artists, audio features):
	- python src/Main/headless_main.py --mode client-top100

- Only run processing for already-fetched Top 100:
	- python src/Main/headless_main.py --mode process-top100

- Simple client search:
	- python src/Main/headless_main.py --mode client-search

User-specific flows (recent, top-tracks/artists) require interactive OAuth and are not supported headlessly without pre-provisioned tokens.

