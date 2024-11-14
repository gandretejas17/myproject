from utility.constants import *
from utility.test_utility import *

"""Model"""
from ..models import Student


class CityTest(BaseTestCase):
    model_class = Student

    @classmethod
    def setUpTestData(self):
        self.user, self.auth_headers = create_user(SUPERUSER_ROLE)


    url = BASE_URL + "students/"
    data = dict()

    # List api test
    def test_get_api_valid(self):
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_api_valid_sort_by(self):
        url = self.url + "?sort_by=id"
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_api_valid_sort_direction(self):
        url = self.url + "?sort_direction=descending"
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_api_valid_page(self):
        url = self.url + "?page=1"
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_api_valid_type(self):
        url = self.url + "?type=all"
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_api_valid_limit(self):
        url = self.url + "?limit=10"
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_api_valid_keyword(self):
        url = self.url + "?keyword=Pune"
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_get_api_valid_state_id(self):
        url = self.url + f"?state={self.state_instance.id}"
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
