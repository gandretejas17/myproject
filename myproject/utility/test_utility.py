from oauth2_provider.models import AccessToken
from django.utils import timezone
from django.utils.timezone import timedelta
import random
import string
from faker import Faker
from oauthlib.common import generate_token
from django.conf import settings
from myapp.model.student import Student
from myapp.model.roles import Roles


from myapp.model.users import User
from django.test import TestCase

from utility.constants import ACCESS_KEY, SUPERUSER_ROLE
from utility.utils import random_number_generator


def get_auth_dict(user):
	expires = timezone.now() + timedelta(
	    seconds=settings.OAUTH2_PROVIDER.get("ACCESS_TOKEN_EXPIRE_SECONDS", 3600)
	)
	access_token = AccessToken.objects.get_or_create(
	    user=user, expires=expires, token=generate_token()
	)
	return {
		"HTTP_AUTHORIZATION": f"Bearer {access_token[0].token}",
		"HTTP_ACCESS_KEY": ACCESS_KEY,
		"content_type": "application/json",
	}
	
def create_user_role():
    role_instance = Roles.objects.create(id=1, name=SUPERUSER_ROLE)
    return role_instance.id

def random_string_generator(stringLength=10):
	letters = string.ascii_lowercase
	return "".join(random.choice(letters) for _ in range(stringLength))

def random_email_generator():
    fake = Faker()
    return fake.email()

def random_number_generator():
    for _ in range(100):
        value = random.randint(50, 10000000000)
        return value

def create_user(role, status=1):

    user, created = User.objects.get_or_create(
        first_name=random_string_generator(),
        last_name=random_string_generator(),
        email=random_email_generator(),
        mobile = f"9{str(random_number_generator())[1:]}",
        role_id=role,
        status=status
    )

    user.set_password("123456")
    user.save()

    auth_headers = get_auth_dict(user)
    
    return user, auth_headers

# def get_address_instance():
#     country_instance, created = Countries.objects.get_or_create(name="India", is_deleted=0)

#     state_instance, created = States.objects.get_or_create(name="Maharashtra", country_id=country_instance.id, is_deleted=0)

#     cities_instance, created = Cities.objects.get_or_create(name="Pune", state_id=state_instance.id, is_deleted=0 )

#     address_instance, created = Addresses.objects.get_or_create(
#         address="Karvenagar", zipcode=411052, is_deleted=0, country_id=country_instance.id, 
#         state_id=state_instance.id, city_id=cities_instance.id
#         )

#     return country_instance, state_instance, cities_instance, address_instance

class BaseTestCase(TestCase):
    # fixtures = ['fixtures/oauth_provider.json','fixtures/myproject.json']
    pass