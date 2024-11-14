import django

django.setup() # don`t write code before django setup

import re
import uuid
import random
import requests
import traceback
from stark_utilities.utilities import *
from utility.constants import (MESSAGES, STATUS_ACTIVE, STATUS_INACTIVE)
from datetime import datetime , timedelta
from oauth2_provider.models import AccessToken, Application, RefreshToken
from oauth2_provider.settings import oauth2_settings
from django.core.mail import EmailMessage
from oauthlib.oauth2.rfc6749.tokens import random_token_generator
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.db import transaction
from cryptography.fernet import Fernet
from django.template.loader import render_to_string
import operator
from functools import reduce
from django.db.models import Q
import uuid
from django.utils import timezone
from datetime import datetime, timedelta
""" mixins to handle request url """


class CreateRetrieveUpdateViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    pass


class MultipleFieldPKModelMixin(object):
    """
    Class to override the default behaviour for .get_object for models which have retrieval on fields
    other  than primary keys.
    """

    lookup_field = []
    lookup_url_kwarg = []

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        get_args = {field: self.kwargs[field] for field in self.lookup_field if field in self.kwargs}

        get_args.update({"pk": self.kwargs[field] for field in self.lookup_url_kwarg if field in self.kwargs})
        return get_object_or_404(queryset, **get_args)



"""Login response """
def get_login_response(user=None, token=None):
    resp_dict = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "mobile": user.mobile,
    }
    if user.role_id:
        resp_dict["role_id"] = user.role_id
        resp_dict["role_name"] = user.role.name

    return resp_dict

def generate_token(request, user):
    expire_seconds = oauth2_settings.user_settings["ACCESS_TOKEN_EXPIRE_SECONDS"]

    scopes = oauth2_settings.user_settings["SCOPES"]

    application = Application.objects.first()
    expires = datetime.now() + timedelta(seconds=expire_seconds)
    access_token = AccessToken.objects.create(
        user=user,
        application=application,
        token=random_token_generator(request),
        expires=expires,
        scope=scopes,
    )

    refresh_token = RefreshToken.objects.create(
        user=user, token=random_token_generator(request), access_token=access_token, application=application
    )

    token = {
        "access_token": access_token.token,
        "token_type": "Bearer",
        "expires_in": expire_seconds,
        "refresh_token": refresh_token.token,
        "scope": scopes,
    }
    return token

def get_pagination_resp(data, request):
    page_response = {"total_count": None, "total_pages": None,
                     "current_page": None, "limit": None}
    if request.query_params.get('type') == 'all':
        return {"data": data}

    page = request.query_params.get('page') or 1
    limit = request.query_params.get('limit') or settings.PAGE_SIZE
    paginator = Paginator(data, limit)
    category_data = paginator.get_page(page).object_list
    page_response = {"total_count": paginator.count, "total_pages": paginator.num_pages,
                     "current_page": page, "limit": limit}
    current_page = paginator.num_pages
    paginator = {"paginator": page_response}
    if int(current_page) < int(page):
        return {"data": [], "paginator": paginator.get('paginator')}
    return {"data": category_data, "paginator": paginator.get('paginator')}

def transform_list(self, data, is_all_data=False, is_dropdown=False):
    if is_all_data:
        return map(self.transform_single_with_to_dict, data)
    elif is_dropdown:
        return map(self.transform_single_with_name, data)    
    else:
        return map(self.transform_single, data)

"""
    :Validate Seializers 
"""
def get_serielizer_error(serializer, with_key=False):
    """handle serializer error"""
    msg_list = []
    try:
        mydict = serializer.errors
        for key in sorted(mydict.keys()):
            msg = ""

            if with_key:
                msg = f"{key} : "

            msg += str(mydict.get(key)[0])

            msg_list.append(msg)
    except Exception:
        msg_list = ["Invalid format"]
    return msg_list


def create_or_update_serializer(serializer_class, data, savepoint=None, instance=None):
    if instance:
        serializer = serializer_class(instance, data=data, partial=True)
    else:
        serializer = serializer_class(data=data)

    if serializer.is_valid():
        serializer.save()
        return  serializer.instance, None
    if savepoint:
        transaction.savepoint_rollback(savepoint)

    return None, get_serielizer_error(serializer)

"""
    : Email Utility
"""

def send_email_otp_forget_password(otp, to_email, template):
    from_emails = settings.FROM_EMAIL
    context = {"otp": otp}
    message = render_to_string(template, context)

    subject = "Account password reset request."

    send_common_email(subject, message, to_email, from_emails)


def send_common_email(subject, message, to_email, from_emails, cc=[], attachment=None):
    try:
        from_emails = settings.FROM_EMAIL

        msg = EmailMessage(subject, message, to=to_email, cc=cc, from_email=from_emails)
        if attachment:
            response = requests.get(attachment)
            msg.attach("", response.content, mimetype="application/pdf")
        
        msg.content_subtype = "html"
        msg.send()

    except Exception as e:
        print("Exception : ",e)


"""
    :Utility Classes
"""

def validate_job_post_dates(job_posted, post_expiring=None):
    try:
        job_posted = datetime.strptime(job_posted, "%Y-%m-%d").date()
        post_expiring = datetime.strptime(post_expiring, "%Y-%m-%d").date()

    except ValueError:
        return "Invalid date format"

    if post_expiring and post_expiring < job_posted:
        return "Job expiring date must be after the job posted date"

    if job_posted < datetime.now().date():
        return "Job posted date should not be in the past"


def validate_birth_date(completion_date, name=None):
    todays_date = datetime.now().date()

    completion_date = datetime.strptime(str(completion_date.get('birth_date')), '%Y-%m-%d').date()

    return (
        f"{name} date should be a past date"
        if completion_date > todays_date
        else None
    )

def validate_display_date(display_date):
    try:
        message = None
        todays_date = datetime.now().date()

        display_date = datetime.strptime(display_date, '%Y-%m-%d').date()

        if display_date < todays_date:
            message = f"Display date should not be a past date"

        return message
    except ValueError as e:
        return "Invalid date format. Please use YYYY-MM-DD."    

def validate_date(completion_date, name=None):
    message = None
    todays_date = datetime.now()
    try:
        completion_date = datetime.strptime(completion_date, '%Y-%m-%d')
    except Exception as e:
        completion_date = datetime.strptime(completion_date, "%Y-%m-%d %H:%M:%S")

    if completion_date < todays_date:
        message = f"{name.replace('_', ' ').capitalize()} date should not be a past date"

    return message


def validate_date_range(valid_from=None, valid_till=None, instance=None):
    try:
        valid_from = datetime.strptime(valid_from, '%Y-%m')
        valid_till = datetime.strptime(valid_till, '%Y-%m')

        return valid_from < valid_till
    except ValueError as e:
        print(e)
        return False

def validate_break_dates(break_from, break_till):
    if break_from is None or break_till is None:
        raise ValueError("Both break from and break till fields are required.")
    try:
        break_from = datetime.strptime(break_from, "%Y-%m-%d")
        break_till = datetime.strptime(break_till, "%Y-%m-%d")
    except ValueError as e:
        return "Invalid date format. Please use YYYY-MM-DD."
    today = datetime.now()

    # Check if 'break_from' is less than 'break_till'
    if break_from >= break_till:
        return "Break from must be before break till."

    # Check if both dates are within the range of today's date
    if today < break_from or today > break_till:
        return "Both break from and break till must be within the range of today's date."


def validate_joining_dates(joining_date):
    try:
        today = datetime.now()
        joining_date = datetime.strptime(joining_date, "%Y-%m-%d")
        if joining_date and joining_date > today:
            return "Enter a previous joining date."
    except ValueError as e:
        return "Invalid date format. Please use YYYY-MM-DD."    

def validate_subscription_dates(starting_date, expiry_date):
    try:
        today = datetime.now()
        starting_date = datetime.strptime(starting_date, "%Y-%m-%d %H:%M:%S.%f")
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S.%f")
        
        if starting_date > expiry_date:
            return "Starting date should be less than expiry date."
        
        if starting_date < today:
            return "Starting date should be greater than or equal to today's date."
   
    except ValueError as e:
        return "Invalid date format."  


class GetInstance:
    def __init__(self, model=None, status=None):
        self.model = model
        self.status = status

    def check_instance_exists(self, ids=None):
        if self.status:
            if instance := self.model.objects.filter(id=ids, status=self.status).first():
                return instance
        elif instance := self.model.objects.filter(id=ids).first():
            return instance
        return None

    def get_instance(self, id=None, is_deleted=None):
        if is_deleted:
            if instance := self.model.objects.filter(id=id, is_deleted=is_deleted).first():
                return instance
        elif instance := self.model.objects.filter(id=id, is_deleted=False).first():
            return instance
        return None

    @staticmethod
    def check_is_duplicate_email_or_mobile(instance, email=None, mobile=None):
        if email:
            if is_user := User.objects.filter(email=email).exclude(id=instance.id).first():
                return 'User with this email already exists'
        if mobile:
            if is_user := User.objects.filter(mobile=mobile).exclude(id=instance.id).first():
                return 'User with this mobile already exists'

def get_instance_from_user(user):
    if user.role_id == JOB_SEEKER_ROLE:
        instance = JobSeekersMeta.objects.filter(user_id=user.id, user__status=STATUS_ACTIVE).first()
    elif user.role_id == EMPLOYER_ROLE:
        instance = Companies.objects.filter(user_id=user.id, user__status=STATUS_ACTIVE).first()
    return instance

def get_object_list(object_list, queryset):
    result = reduce(lambda x, y: x | y, object_list)
    return queryset if (queryset := queryset.filter(result)) else None

""" 
    :Data Validation
"""

def validate_cin_number(cin_number):
    cin_pattern = r'^[A-Z]{1}[A-Z0-9]{4}[0-9]{6}[A-Z0-9]{3}[0-9]{1}$'
    return bool(re.match(cin_pattern, cin_number))

def validate_website_url(url):
    url_pattern = r'^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}(/[\S]*)?$'
    return bool(re.match(url_pattern, url))

def is_valid_email(email):
    pattern = r'^[^0-9][a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_integer_field(args_list) -> any:
    for key, value in args_list:
        if value and not isinstance(value, int):
            return f"{key.replace('_', ' ').capitalize()} value should be an integer."  

def validate_numeric_values(args_list) -> any:
    for key, value in args_list:                     
        if value and value < 0:
            return f"{key.replace('_', ' ').capitalize()} must be a valid number."        
    return None

def validate_mobile_number(args, req_data):
    for key, value in args.items():
        if not key in req_data:
            pass
        elif not value.isdigit():
            return f"Please add a valid {key.replace('_', ' ')}."        
        elif not value:
            return f"{key.replace('_', ' ').capitalize()} cannot be empty."
        
        elif value.strip() and value[0] not in ['6', '7', '8', '9'] or len(value) != 10:
            return f"Please add a valid {key.replace('_', ' ')}."

def validate_strings_data(data_dict, req_data):
    for key, value in data_dict.items():
        if not key in req_data:
            pass
        elif value and not str(value).strip():
            return f"{key.replace('_', ' ').capitalize()} cannot be empty."
        elif not value:
            return f"{key.replace('_', ' ').capitalize()} cannot be empty."
        
        elif value.replace(' ', '') and not value.replace(' ', '').isalpha():
                return f"{key.replace('_', ' ').capitalize()} should not contain special characters."

def validate_empty_strings(data_dict, req_data):
    for key,value in data_dict.items():
        if not key in req_data:
            pass
        elif value and not str(value).strip():
            return f"{key.replace('_', ' ').capitalize()} cannot be empty."
        elif not value:
            return f"{key.replace('_', ' ').capitalize()} cannot be empty."

def validate_enum_fields(validations):
    for value, valid_set, error_message in validations:
        if value and value not in valid_set:
            return f"Invalid {error_message}."

def get_required_fields(required_fields, data_dict):
    for key in required_fields:
        if not key.strip() or not data_dict.get(key):
            return f"{key.replace('_', ' ').capitalize()} is required."

def is_valid_grade(grades):
    grade_regex = r'^[A-Z][+-]?$'
    return bool(re.match(grade_regex, grades))

def validate_patent_application_number(application_number):
    patent_regex = r'^\d{4}[1-4][1-9][0-9]{6}$'
    return bool(re.match(patent_regex, application_number))

def is_boolean(args,req_data):
    for key, value in args:
        if not key in req_data:
            pass
        elif not isinstance(value, bool):
            return f"Invalid {key.replace('_', ' ')}."

def trim_data(args) -> str:
    for key, value in args.items():
        value = value.strip()
        if not value:
            return f"{key.replace('_', ' ').capitalize()} cannot be empty."

def is_valid_gstin(gstin_number):
    gstin_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return bool(re.match(gstin_pattern, gstin_number))

def filter_json_data(string_list, field, req_data):
    if not field in req_data:
        return None
    try:
        if isinstance(string_list[0], int):
            string_list = map(str, string_list) 
            string_list = (list(string_list))

        for value in string_list:
            if not value:
                return f"{field.replace('_', ' ').capitalize()} is invalid."
            elif isinstance(string_list, list) and not value.strip():
                return f"{field.replace('_', ' ').capitalize()} is invalid."
    except Exception:
        return f"Invalid {field.replace('_', ' ')}."

"""
    :Generate ranerate code
"""

def get_delay_time():
    return datetime.now() + timedelta(minutes=1)

def generate_otp_number() -> int:
    range_start = 10 ** (settings.OTP_LENGTH - 1)
    range_end = (10 ** settings.OTP_LENGTH) - 1
    return randint(range_start, range_end)

def generate_application_id() -> int:
    return random.randint(10**9, (10**10) - 1)

def encrypt_subscription_no(subscription_no):
    fernet_key = Fernet.generate_key()
    fernet_cipher = Fernet(fernet_key)
    encrypted_id = fernet_cipher.encrypt(subscription_no.encode())
    return encrypted_id.decode()

# def create_subscription_no():
#     subscription_no = str(uuid.uuid4())
#     return encrypt_subscription_no(subscription_no) 

def create_subscription_no():
    return str(uuid.uuid4().hex[:22])

def generate_expiry_date(instance, role):
    if role.id == SUPERUSER_ROLE or role.parent_id == MF_USER_ROLE:
        duration = instance.plan_duration 
    else:
        duration = instance.subscription_plan.plan_duration    

    if duration == 1:
        expiry_date = datetime.now() + timedelta(days=1)
    elif duration == 2:
        expiry_date = datetime.now() + timedelta(days=7)
    elif duration == 3:
        expiry_date = datetime.now() + timedelta(days=15)         
    elif duration == 4:
        expiry_date = datetime.now() + timedelta(days=30) 
    elif duration == 5:
        expiry_date = datetime.now() + timedelta(days=90)
    elif duration == 6:
        expiry_date = datetime.now() + timedelta(days=180)
    elif duration == 7:
        expiry_date = datetime.now() + timedelta(days=270)
    elif duration == 8:
        expiry_date = datetime.now() + timedelta(days=365)
    else:
        raise ValueError("Invalid plan duration")

    return expiry_date


def generate_total_amount(instance):
    discount_percentage = instance.discount
    price = instance.price
    
    discount_amount = price * (discount_percentage / 100)
    
    amount = price - discount_amount
    
    gst_amount = amount * (ESTIMATED_GST / 100)
    
    total_amount = (amount + gst_amount) 
    
    return total_amount


def generate_transaction_id():
    """
    Generate a unique payment transaction ID based on timestamp and UUID.
    """
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')  # Current timestamp with microsecond precision
    unique_id = str(uuid.uuid4().hex)[:12]  # Generate a UUID and take the first 12 characters
    transaction_id = f"{timestamp}{unique_id}"
    return transaction_id

def random_number_generator() -> int:
    return random.randint(10**9, (10**10) - 1)

"""list filters"""
def filter_array_list(filter_array, where_array, obj_list):
    for key, value in filter_array.items():
        if key in where_array.keys():
            val = where_array[key]
            obj_list.append((value, val))

    return obj_list

def get_end_date(datem):
    year = 0
    if datem.month == 12:
        year = 1
    return datetime(datem.year + year, (datem + relativedelta(months=1)).month, 1) - timedelta(days=1)

def filter_date(start_date, end_date, obj_list):
    if start_date and end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = datetime.combine(end_date, datetime.max.time())
        obj_list.append(["created_at__range", [start_date, end_date]])

    elif start_date:
        obj_list.append(["created_at__gte", start_date])

    elif end_date:
        obj_list.append(["created_at__lte", end_date])
    
    return obj_list


def filter_queryset(request, where_array):
    try:
        obj_list = []
        sort_by = where_array.get("sort_by", "id")
        sort_direction = where_array.get("sort_direction", "ascending")
        
        if sort_direction == "descending":
            sort_by = f"-{sort_by}"
    
        start_date = where_array.get('start_date')
        end_date = where_array.get('end_date')
        if start_date and end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = datetime.combine(end_date, datetime.max.time())
            obj_list.append(["created_at__range", [start_date, end_date]])
    
        elif start_date:
            obj_list.append(["created_at__gte", start_date])
    
        elif end_date:
            obj_list.append(["created_at__lte", end_date])
        
        return obj_list, sort_by, None
    
    except Exception as e:
        return None, None , e

def filter_status(where_array):
    obj_list = []
    if where_array.get("status"):
        status = int(where_array.get("status"))
        if status in [STATUS_INACTIVE, STATUS_ACTIVE]:
            obj_list.append(("status", status))
        else:
            return None, MESSAGES['invalid_status']
    return obj_list, None


def get_receiver_ids(is_employer, is_job_seeker, user_ids, employer_user_ids, jobseeker_user_ids):
    if (is_employer and is_job_seeker) == True:
        return employer_user_ids and jobseeker_user_ids
    elif is_employer == True:
        return employer_user_ids
    elif is_job_seeker == True:
        return jobseeker_user_ids
    else:
        return user_ids

def get_receiver_emails(is_employer, is_job_seeker, user_emails ,employer_user_emails, jobseeker_user_emails):
    if (is_employer and is_job_seeker) == True:
        return employer_user_emails and jobseeker_user_emails
    elif is_employer == True:
        return employer_user_emails
    elif is_job_seeker == True:
        return jobseeker_user_emails
    else:
        return user_emails  
        
def get_job_status_filter(inprogress_jobs, behind_jobs, queryset): 
    current_date = datetime.now().date()    
    
    approved_jobs_queryset = queryset.filter(job_status=JOB_APPROVED)
    completed_jobs_queryset = queryset.filter(job_status=JOB_COMPLETED)

    combined_queryset = approved_jobs_queryset | completed_jobs_queryset    
    
    if inprogress_jobs:
        queryset = combined_queryset.filter(job_status=JOB_APPROVED, post_expiring__gte=current_date)
        
    elif behind_jobs:
        queryset = combined_queryset.filter(job_status=JOB_APPROVED, post_expiring__lt=current_date)
        
    return queryset


def decrease_cv_access_count(user, action):
    from job_portal_app.models import Subscriptions
    """
        Decrease the cv access count from the subscription
    """
    try:
        if action not in [VIEW_PROFILE, DOWNLOAD_CV]:
            return "Invalid action performed"
        subscription = None
        if subscriptions := Subscriptions.objects.filter(user_id=user.id, status=STATUS_ACTIVE):
            for subscription in subscriptions:
                if subscription.subscription_plan.cv_access:
                    if subscription.cv_access_count and subscription.cv_access_count >= 1:
                        break
            if subscription.cv_access_count <= 0:
                return False, "You have exceeded the cv access limit"

            if action == VIEW_PROFILE:
                subscription.cv_access_count -= 1
            elif action == DOWNLOAD_CV:
                subscription.cv_access_count -= 2
            subscription.save()
            return True, False
        else:    
            return False, PERMISSION_UNAUTHORISED
    except Exception:
        print("traceback", traceback.format_exc())

def decrease_hot_job_count(user):
    from job_portal_app.models import Subscriptions
    """
        Decrease the hot job count from the subscription
    """
    try:
        subscription = None
        if subscriptions := Subscriptions.objects.filter(user_id=user.id, status=STATUS_ACTIVE):
            for subscription in subscriptions:
                if subscription.subscription_plan.no_of_in_demand_requisition:
                    if subscription.no_of_in_demand_requisition_count and subscription.no_of_in_demand_requisition_count >= 1:
                        break
            if subscription.no_of_in_demand_requisition_count <= 0:
                return False, "You have exceeded hot job limit"
            else:    
                subscription.no_of_in_demand_requisition_count -= 1
                subscription.save()
                return True, False
        else:    
            return False, PERMISSION_UNAUTHORISED
    except Exception:
        print("traceback", traceback.format_exc())


# from geopy.geocoders import Nominatim
# from geopy.exc import GeocoderTimedOut

def get_city_name(latitude, longitude):
    geolocator = Nominatim(user_agent="city_fetcher")
    try:
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
    except GeocoderTimedOut:
        return "Geocoder service timed out"  # Handle timeout errors gracefully

    if location is None:
        return "City not found"  # Handle case when location is None

    address = location.raw['address']
    city = address.get('state_district', '')

    if not city:
        city = address.get('town', '')

    if not city:
        city = address.get('village', '')

    if not city:
        city = address.get('state', '')

    return city


""" PDF Generation """
from django.template.loader import get_template
# from xhtml2pdf import pisa
from io import BytesIO

def render_to_pdf(template_src, context_dict={}):
    try:
        template = get_template(template_src)
        html = template.render(context_dict)
        result = BytesIO()
        encoded_html = html.encode("utf-8")
        pdf = pisa.pisaDocument(BytesIO(encoded_html), result)
        
    except Exception as e:
        print("Error:",e)
        print(traceback.format_exc(), " ----")
    if not pdf.err:
        return result.getvalue()
    return None

def get_profile_completion(job_seeker):
    completion_count = 0
    (personal_details_percentage, address_percentage, educational_details_percentage, professional_experience_percentage, 
        preference_placement_percentage, skills_percentage, lecture_percentage,
        attachment_percentage, awards_percentage) = 0,0,0,0,0,0,0,0,0
    
    total_sections = 9
    percent = 100/total_sections
    
    try:
        if job_seeker.user:
            personal_details_percentage = percent
        
        if job_seeker.user.address:
            address_percentage = percent
            
        if job_seeker.job_seeker_education.exists():
            educational_details_percentage = percent
            
        if job_seeker.job_seeker_employment_details.exists():
            professional_experience_percentage = percent                        
                    
        if job_seeker.job_seeker_career_preferences.exists():
            preference_placement_percentage = percent 
          
        if job_seeker.job_seeker_job_seeker_key_skills.exists():
            skills_percentage = percent           
            
        if job_seeker.job_seeker_lectures.exists():
            lecture_percentage = percent               
            
        if job_seeker.resume and job_seeker.profile_image:
            attachment_percentage = percent
        
        elif job_seeker.resume or job_seeker.profile_image:
            attachment_percentage = percent/2
        
        if job_seeker.awards:
            awards_percentage = percent       
                                                      
        completion_count = round((personal_details_percentage + educational_details_percentage + 
                            professional_experience_percentage + preference_placement_percentage + 
                            address_percentage + skills_percentage + lecture_percentage +
                            awards_percentage + attachment_percentage))
        return min(completion_count, 100)
    
    except Exception:
        print("Exception ", traceback.format_exc())
        
        
from django.db.models import Count

def get_demanding_categories_jobs(queryset):
    
    queryset = queryset.filter(job_status=JOB_APPROVED)
    
    specialization_counts = queryset.values('specialization').annotate(
        specialization_count=Count('specialization')).order_by('-specialization_count')
    
    specialization_order = {spec['specialization']: order for order, spec in enumerate(specialization_counts, start=1)}
    
    queryset = sorted(queryset, key=lambda x: specialization_order.get(x.specialization_id, float('inf')))
          
    return queryset


def decrease_recruiter_count(instance, user):
    """
        Decrease the recruiter count from the subscription
    """
    try:
        subscriptions = None
        if subscriptions := Subscriptions.objects.filter(user_id=user.id, status=STATUS_ACTIVE):
            for subscription in subscriptions:
                if subscription.subscription_plan.recruiters:
                    if subscription.recruiters_count and subscription.recruiters_count >= 1:
                        break
            if subscription.recruiters_count <= 0:
                return False, "You have exceeded the recruiter access limit"
    
            if instance.is_initiate and instance.job_application:
                subscription.recruiters_count -= 1
            subscription.save()
            return True, False
        else:    
            return False, PERMISSION_UNAUTHORISED
    
    except Exception as e:
        print("traceback", traceback.format_exc())
        raise e.args[0]
    
    
def decrease_email_count(instance, user):
    """
        Decrease the email count from the subscription
    """
    try:
        subscription = None
        if subscriptions := Subscriptions.objects.filter(user_id=user.id, status=STATUS_ACTIVE):
            for subscription in subscriptions:
                if subscription.subscription_plan.emails:
                    if subscription.emails_sent and subscription.emails_sent >= 1:
                        break
            if subscription.emails_sent <= 0:
                return False, "You have exceeded the email access limit"
    
            if instance:
                subscription.emails_sent -= 1
            subscription.save()
            return True, False
        else:    
            return False, PERMISSION_UNAUTHORISED
    
    except Exception as e:
        print("traceback", traceback.format_exc())
        raise e.args[0]    
    
    
def apply_foreign_key_filters(queryset, where_array, filter_mapping):
    for key, field_name in filter_mapping.items():
        if value := where_array.get(key):
            ids = [int(id) for id in value.strip('[]').split(',')]
            queryset = queryset.filter(**{f'{field_name}__in': ids})

    return queryset


def apply_enum_filters(where_array, field_mapping):
    obj_list = []
    for field, lookup in field_mapping.items():
        if values := where_array.get(field):
            value_list = values.strip('[]').replace("'", "").split(',')
            obj_list.append(Q(**{f'{lookup}__in': value_list}))
    return obj_list


def get_calendar_filter(calendar, queryset, start_date, end_date):
    """
        Filter the queryset based on the calendar values
    """    
    calendar = int(calendar)
    job_queryset = queryset.exclude(job_status=JOB_DELETED)
    calendar_queryset = []

    current_date = datetime.now().date()
    current_week =  current_date - timedelta(days=current_date.weekday())
    current_week_start = current_date - timedelta(days=current_date.weekday())

    # Calculate the last day of the current week (Sunday)
    current_week_end = current_week_start + timedelta(days=6)

    current_month = current_date.month
    last_month = current_month - 1 if current_month > 1 else 12
    current_year = current_date.year 
    
    if calendar == THIS_WEEK:
        calendar_queryset = job_queryset.filter(post_expiring__gte=current_week_start, post_expiring__lte=current_week_end)
        
        # calendar_queryset = job_queryset.filter(created_at__gte=current_week)
    elif calendar == THIS_MONTH:
        calendar_queryset = job_queryset.filter(created_at__month=current_month)
    elif calendar == LAST_MONTH:
        calendar_queryset = job_queryset.filter(created_at__month=last_month)
    elif calendar == THIS_YEAR:
        calendar_queryset = job_queryset.filter(created_at__year=current_year)
        
    elif calendar == CUSTOM_DATE:                
        obj_list = []
        if start_date and end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = datetime.combine(end_date, datetime.max.time())
            obj_list.append(["created_at__range", [start_date, end_date]])
                
        if q_list := [Q(x) for x in obj_list]:
            calendar_queryset = job_queryset.filter(reduce(operator.and_, q_list))
                        
    return calendar_queryset  


def get_user_calendar_filter(calendar, queryset, start_date, end_date):
    """
        Filter the queryset based on the calendar values
    """    
    calendar = int(calendar)
    user_queryset = queryset.filter(user__status__in=[STATUS_ACTIVE, STATUS_INACTIVE])
    calendar_queryset = []

    current_date = datetime.now().date()
    current_week =  current_date - timedelta(days=current_date.weekday())
    current_week_start = current_date - timedelta(days=current_date.weekday())

    # Calculate the last day of the current week (Sunday)
    current_week_end = current_week_start + timedelta(days=6)    
    
    current_month = current_date.month
    last_month = current_month - 1 if current_month > 1 else 12
    current_year = current_date.year 
    
    if calendar == THIS_WEEK:
        calendar_queryset = user_queryset.filter(created_at__gte=current_week_start, created_at__lte=current_week_end)
    elif calendar == THIS_MONTH:
        calendar_queryset = user_queryset.filter(created_at__month=current_month)
    elif calendar == LAST_MONTH:
        calendar_queryset = user_queryset.filter(created_at__month=last_month)
    elif calendar == THIS_YEAR:
        calendar_queryset = user_queryset.filter(created_at__year=current_year)
        
    elif calendar == CUSTOM_DATE:                
        obj_list = []
        if start_date and end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = datetime.combine(end_date, datetime.max.time())
            obj_list.append(["created_at__range", [start_date, end_date]])
                
        if q_list := [Q(x) for x in obj_list]:
            calendar_queryset = user_queryset.filter(reduce(operator.and_, q_list))
                        
    return calendar_queryset 


def get_job_application_calendar_filter(calendar, queryset, start_date, end_date):
    """
        Filter the queryset based on the calendar values
    """    
    calendar = int(calendar)
    job_application_queryset = queryset.filter(status__in=[STATUS_ACTIVE, STATUS_INACTIVE])
    calendar_queryset = []

    current_date = datetime.now().date()
    current_week =  current_date - timedelta(days=current_date.weekday())
    current_week_start = current_date - timedelta(days=current_date.weekday())

    # Calculate the last day of the current week (Sunday)
    current_week_end = current_week_start + timedelta(days=6)    
    
    current_month = current_date.month
    last_month = current_month - 1 if current_month > 1 else 12
    current_year = current_date.year 
    
    if calendar == THIS_WEEK:
        calendar_queryset = job_application_queryset.filter(created_at__gte=current_week_start, created_at__lte=current_week_end)
    elif calendar == THIS_MONTH:
        calendar_queryset = job_application_queryset.filter(created_at__month=current_month)
    elif calendar == LAST_MONTH:
        calendar_queryset = job_application_queryset.filter(created_at__month=last_month)
    elif calendar == THIS_YEAR:
        calendar_queryset = job_application_queryset.filter(created_at__year=current_year)
        
    elif calendar == CUSTOM_DATE:                
        obj_list = []
        if start_date and end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = datetime.combine(end_date, datetime.max.time())
            obj_list.append(["created_at__range", [start_date, end_date]])
                
        if q_list := [Q(x) for x in obj_list]:
            calendar_queryset = job_application_queryset.filter(reduce(operator.and_, q_list))
                        
    return calendar_queryset 

def get_field_type(model, field):
    try:
        field_type = None
        field = model._meta.get_field(field)
        if field in model._meta.fields:
            field_type = type(field).__name__

        return field_type
    except Exception:
        return None
    
    
    
import gzip
import json
from io import BytesIO
 
def gzip_compress_json_response(data):
    json_str = json.dumps(data)
    json_bytes = json_str.encode('utf-8')
    buffer = BytesIO()
    with gzip.GzipFile(mode='wb', fileobj=buffer) as gzip_file:
        gzip_file.write(json_bytes)
    
    return buffer.getvalue()        