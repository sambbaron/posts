class DevelopmentConfig(object):
    DATABASE_URI = "postgresql://action:action@localhost:5432/posts"
    DEBUG = True

class TestingConfig(object):
    DATABASE_URI = "postgresql://action:action@localhost:5432/posts_test"
    DEBUG = True
