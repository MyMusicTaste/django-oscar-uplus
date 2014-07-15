
from oscar.app import Shop

from apps.uplus.app import application as checkout_app


class HandocApp(Shop):
    checkout_app = checkout_app
application = HandocApp()
