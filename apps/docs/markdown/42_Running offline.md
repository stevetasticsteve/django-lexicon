The Lexicon app is currently hosted at https://lexicon.reachkovol.com

The app can be run locally (offline) using docker or podman on Linux.

- Download the latest [docker-compose.yml](https://github.com/stevetasticsteve/django-lexicon/blob/master/docker/docker-compose.prod.yml)
- Create a folder 
- Prepare a [.env file](https://github.com/stevetasticsteve/django-lexicon/blob/master/docker/.env-example)
- Add the .env file to the folder
- docker compose up -d
- Create a superuser with 'docker exec -it lexicon_app1 uv run manage.py createsuperuser'

These steps should bring the containers up, restart them at boot and even update them automatically using watchtower. The Lexicon app containers use uv to manage their python environment.

The docker-compose file is configured to bind to localhost port 8000 so a reverse proxy like nginx is required, or modifying the docker-compose.