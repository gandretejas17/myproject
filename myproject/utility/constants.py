
BASE_URL = 'http://127.0.0.1:8000/api/'

FILE_SIZE = 5
BITS_PER_BYTE = 8
BYTES_PER_MB = 1048576

"""Status"""
STATUS_ACTIVE = 1
STATUS_INACTIVE = 2
STATUS_DELETED = 3 

""" Roles """
SUPERUSER_ROLE = 1

"""Messages"""
MESSAGES = {
    "username_password_required": "Username and password are required. ",
    "invalid_username_and_password": "Invalid username or password. Please try again.",
    "email_not_provided": "Email not provided.",
    "forget_password_email_subject": "Medforage Reset Password",
    "send_email_otp_email_subject": "OTP for email verification",
    "password_confirm_password_invalid": "Password and confirm password does not match.",
    "created": " created successfully.",
    "updated": " updated successfully.",
    "deleted": " deleted successfully.",
    "not_found": " not found.",
    "email_not_exist":"Email not exists.",
    "username_not_exist":"Username not exists.",
    "user_inactive":"User is inactive.",
    "user_deleted":"User is deleted.",
    "all_fields_should_not_empty" : "All fields should not be empty",
    "invalid_status": "Invalid status.",
    "forbidden" : "You are not allowed to perform this action.",
    "already_exists": " already exists.",
    "invalid_blog_category":"Invalid blog category.",
    "invalid_notice_period":"Invalid notice period.",
    "user_not_exists": "User does not exist.",
    "permission_denied": "Permission denied.",
    "invalid_work_status":"Invalid work status."
}