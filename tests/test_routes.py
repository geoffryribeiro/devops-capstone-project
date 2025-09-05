"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

# Define a URI padrão para o banco de dados PostgreSQL
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # Clean up previous tests
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    ######################################################################
    # H E L P E R   M E T H O D S
    ######################################################################
    def _create_account(self):
        """Helper method to create a test account"""
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.get_json()

    ######################################################################
    # T E S T   E N D P O I N T S
    ######################################################################
    def test_index(self):
        """It should return the home page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should return health status"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["status"], "OK")

    def test_create_account(self):
        """It should create a new account"""
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()
        self.assertEqual(data["name"], account.name)

    def test_list_accounts(self):
        """It should list all accounts"""
        self._create_account()
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.get_json()), 1)

    def test_get_account(self):
        """It should retrieve a single account"""
        account = self._create_account()
        response = self.client.get(f"{BASE_URL}/{account['id']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["id"], account["id"])

    def test_update_account(self):
        """It should update an existing account"""
        account = self._create_account()
        account["name"] = "Updated Name"
        response = self.client.put(f"{BASE_URL}/{account['id']}", json=account)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["name"], "Updated Name")

    def test_delete_account(self):
        """It should delete an account"""
        account = self._create_account()
        response = self.client.delete(f"{BASE_URL}/{account['id']}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_nonexistent_account(self):
        """It should return 404 for non-existent account"""
        response = self.client.get(f"{BASE_URL}/999999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_nonexistent_account(self):
        """It should return 404 when updating non-existent account"""
        account = AccountFactory().serialize()
        response = self.client.put(f"{BASE_URL}/999999", json=account)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_account(self):
        """It should return 204 when deleting non-existent account"""
        response = self.client.delete(f"{BASE_URL}/999999")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_bad_request(self):
        """It should return 400 for invalid account creation"""
        response = self.client.post(BASE_URL, json={"name": "incompleto"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should return 415 for wrong content type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="text/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    ######################################################################
    # T E S T   S E C U R I T Y   H E A D E R S
    ######################################################################
    def test_security_headers(self):
        """It Should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'self'; object-src 'none'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    def test_cors_security(self):
        """It must return a CORS header"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')
