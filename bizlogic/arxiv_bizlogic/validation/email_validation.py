
import re

email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

def is_valid_email(email: str) -> bool:
  """
  Checks if a given string is a valid email address using a regular expression.

  Args:
    email: The string to validate.

  Returns:
    True if the email is valid, False otherwise.
  """
  return bool(re.fullmatch(email_regex, email))
