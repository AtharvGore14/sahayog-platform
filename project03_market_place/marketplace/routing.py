from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/bidding/(?P<listing_id>\d+)/$', consumers.BiddingConsumer.as_asgi()),
]