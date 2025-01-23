import smtplib
from email.utils import formatdate

current_date = formatdate(localtime=True)

server = smtplib.SMTP('localhost', 21508)

# Include the Date header in the message
message = f"""\
Date: {current_date}
From: sender@example.com
To: receiver@example.com
Subject: Test Email

This is a test email.
"""

# Send the email
server.sendmail(
    from_addr="sender@example.com",
    to_addrs=["receiver@example.com"],
    msg=message
)
server.quit()
