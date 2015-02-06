import unittest
import os
import json
from urlparse import urlparse

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the posts API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)
        
    def testGetEmptyPosts(self):
        """ Getting posts from an empty database """
        response = self.client.get("/api/posts",
            headers=[("Accept", "application/json")]
        )
        
        # Test request to endpoint
        self.assertEqual(response.status_code, 200)
        # Test returning JSON
        self.assertEqual(response.mimetype, "application/json")
        # Test endpoint returns empty list
        data = json.loads(response.data)
        self.assertEqual(data, [])
        
    def testGetPosts(self):
        """ Getting posts from a populated database """
        
        # Add new posts
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")
        session.add_all([postA, postB])
        session.commit()        
        
        # Routed from api.py and push accept header
        response = self.client.get("/api/posts",
            headers=[("Accept", "application/json")]
        )
        
        # Test response status and type
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        
        # Set JSON data response and test number of responses
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

        # Test content of postA
        postA = data[0]
        self.assertEqual(postA["title"], "Example Post A")
        self.assertEqual(postA["body"], "Just a test")
        # Test content of postB
        postB = data[1]
        self.assertEqual(postB["title"], "Example Post B")
        self.assertEqual(postB["body"], "Still a test")
        
    def testGetPost(self):
        """ Getting a single post from a populated database """
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts/{}".format(postB.id),
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        post = json.loads(response.data)
        self.assertEqual(post["title"], "Example Post B")
        self.assertEqual(post["body"], "Still a test")

    def testGetNonExistentPost(self):
        """ Getting a single post which doesn't exist """
        response = self.client.get("/api/posts/1",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Could not find post with id 1")
        
    def testUnsupportedAcceptHeader(self):
        response = self.client.get("/api/posts",
            headers=[("Accept", "application/xml")]
        )

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"],
                         "Request must accept application/json data")
        
    def testDeletePost(self):
        """ Delete a single post from a populated database """
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()

        response = self.client.delete("/api/posts/{}".format(postB.id),
            headers=[("Accept", "application/json")]
        )        

        # Test one post deleted/one post remaining
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        # Test response status, message, and mimetype
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(data["message"], "Post 2 deleted")

    def testGetPostsWithTitle(self):
        """ Filtering posts by title 
            Test posts that include 'whistle' in title """
        
        # Add three posts - two contain whistle
        postA = models.Post(title="Post with bells", body="Just a test")
        postB = models.Post(title="Post with whistles", body="Still a test")
        postC = models.Post(title="Post with bells and whistles",
                            body="Another test")

        session.add_all([postA, postB, postC])
        session.commit()

        # Route using query string
        response = self.client.get("/api/posts?title_like=whistles",
            headers=[("Accept", "application/json")]
        )
        # Test response status code and mimetype
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        # Test number of posts
        posts = json.loads(response.data)
        self.assertEqual(len(posts), 2)
        # Test first post content
        post = posts[0]
        self.assertEqual(post["title"], "Post with whistles")
        self.assertEqual(post["body"], "Still a test")
        # Test second post content
        post = posts[1]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "Another test")        
        
    def testGetPostsWithBody(self):
        """ Filtering posts by body 
            Test posts that include 'bells' in body """
        
        # Add three posts - two contain whistle
        postA = models.Post(title="Just a test", body="Post with bells")
        postB = models.Post(title="Still a Test", body="Post with whistles")
        postC = models.Post(title="Another Test",
                            body="Post with bells and whistles")

        session.add_all([postA, postB, postC])
        session.commit()

        # Route using query string
        response = self.client.get("/api/posts?body_like=bells",
            headers=[("Accept", "application/json")]
        )
        # Test response status code and mimetype
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        # Test number of posts
        posts = json.loads(response.data)
        self.assertEqual(len(posts), 2)
        # Test first post content
        post = posts[0]
        self.assertEqual(post["title"], "Just a test")
        self.assertEqual(post["body"], "Post with bells")
        # Test second post content
        post = posts[1]
        self.assertEqual(post["title"], "Another Test")
        self.assertEqual(post["body"], "Post with bells and whistles")        

                
    def testGetPostsWithTitleAndBody(self):
        """ Filtering posts by title and body 
            Test posts that include 'Just' in title and 'bells' in body """
        
        # Add three posts - two contain whistle
        postA = models.Post(title="Just a test", body="Post with bells")
        postB = models.Post(title="Still a Test", body="Post with whistles")
        postC = models.Post(title="Another Test",
                            body="Post with bells and whistles")

        session.add_all([postA, postB, postC])
        session.commit()

        # Route using query string
        response = self.client.get("/api/posts?title_like=Just&body_like=bells",
            headers=[("Accept", "application/json")]
        )
        # Test response status code and mimetype
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        # Test number of posts
        posts = json.loads(response.data)
        self.assertEqual(len(posts), 1)
        # Test first post content
        post = posts[0]
        self.assertEqual(post["title"], "Just a test")
        self.assertEqual(post["body"], "Post with bells")
        
    def testPostPost(self):
        """ Posting a new post """
        data = {
            "title": "Example Post",
            "body": "Just a test"
        }
        
        # Create POST request using JSON from 'data' dictionary
        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        # Test response code, mimetype, and location path
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/posts/1")

        # Test post content from response
        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Example Post")
        self.assertEqual(data["body"], "Just a test")

        # Query post from database
        posts = session.query(models.Post).all()
        self.assertEqual(len(posts), 1)
        # Test post content from database
        post = posts[0]
        self.assertEqual(post.title, "Example Post")
        self.assertEqual(post.body, "Just a test")        

    def testUnsupportedMimetype(self):
        """Test unsupported mimetype with XML"""
        data = "<xml></xml>"
        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/xml",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"],
                         "Request must contain application/json data")

    def testInvalidData(self):
        """ Posting a post with an invalid body """
        data = {
            "title": "Example Post",
            "body": 32
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "32 is not of type 'string'")

    def testMissingData(self):
        """ Posting a post with a missing body """
        data = {
            "title": "Example Post",
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "'body' is a required property")        
        
if __name__ == "__main__":
    unittest.main()
