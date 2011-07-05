config = dict(
    MZALENDO_DB_NAME = 'mzalendo',    # Name of your postgres database
    MZALENDO_DB_USER = '',            # Postgres user to connect with
    MZALENDO_DB_PASS = '',            # Password for postgres
    MZALENDO_DB_HOST = 'localhost',   # host for postgres
    MZALENDO_DB_PORT = 5432,          # port for postgres
    
    # Set this to some random stuff yourself
    DJANGO_SECRET_KEY = 'FIXME',

    TIME_ZONE = 'Europe/London',
    # TIME_ZONE = 'Africa/Nairobi',

    STAGING = '1',
)
