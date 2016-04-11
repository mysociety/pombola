# Pombola on Heroku

## Running locally

Example `.env` file:

```
ON_HEROKU=1
HEROKU_LOCAL=1
DATABASE_URL='postgres://mark@/pombola-nigeria'
```

Then it should work with `heroku local`.

## Deploying to Heroku

### Automatic

The simplest way to deploy Pombola to Heroku is to click one of the following buttons depending on which country you'd like to deploy.

- [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?env[COUNTRY_APP]=kenya) - Kenya
- [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?env[COUNTRY_APP]=south_africa) - South Africa

### Manual

To create it on heroku, try:

```
heroku create pombola-kenya --buildpack https://github.com/ddollar/heroku-buildpack-multi.git
```

Set environment variables:

```
heroku config:set CONFIG_FROM_ENV=True
heroku config:set COUNTRY_APP=kenya
heroku config:set ON_HEROKU=1
heroku config:set DJANGO_SECRET_KEY='put-a-new-securely-generated-random-string-here'
heroku config:set STAGING=True
heroku config:set DISABLE_COLLECTSTATIC=1
```

Deploy with:

```
git push heroku heroku:master
```
