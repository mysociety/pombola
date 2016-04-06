Example `.env` file:

```
ON_HEROKU=1
HEROKU_LOCAL=1
DATABASE_URL='postgres://mark@/pombola-nigeria'
```

Then it should work with `heroku local`.

To create it on heroku, try:

```
heroku create pombola-kenya
```

Set the special multiple buildpacks buildpack:

```
heroku buildpacks:set https://github.com/ddollar/heroku-buildpack-multi.git
```

Set environment variables:

```
heroku config:set CONFIG_FROM_ENV=True
heroku config:set COUNTRY_APP=kenya
heroku config:set ON_HEROKU=1
heroku config:set DJANGO_SECRET_KEY='put-a-new-securely-generated-random-string-here'
heroku config:set STAGING=True
```

Possibly need to manually specify the PostgreSQL addon?

```
heroku addons:create heroku-postgresql:hobby-dev
```

Redploy with:

```
git push heroku heroku:master
```
