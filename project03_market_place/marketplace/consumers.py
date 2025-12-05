import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Bid, SupplyListing
from .serializers import BidSerializer

# We need these imports for the signal
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class BiddingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.listing_id = self.scope['url_route']['kwargs']['listing_id']
        self.room_group_name = f'listing_{self.listing_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # This is the event handler that sends the message to the client
    async def new_bid(self, event):
        await self.send(text_data=json.dumps(event['bid']))


# This is the signal receiver that gets triggered when a Bid is saved
@receiver(post_save, sender=Bid)
def announce_new_bid(sender, instance, created, **kwargs):
    # The "if created:" line has been removed.
    # This function will now run every time a bid is saved.
    channel_layer = get_channel_layer()
    serializer = BidSerializer(instance)
    async_to_sync(channel_layer.group_send)(
        f'listing_{instance.listing.id}',
        {
            "type": "new.bid", # This calls the new_bid method above
            "bid": serializer.data
        }
    )