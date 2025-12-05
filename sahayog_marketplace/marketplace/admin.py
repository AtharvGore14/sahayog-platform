from django.contrib import admin
from .models import Commodity, SupplyListing, Bid, Deal

class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    readonly_fields = ('bidder', 'amount', 'timestamp')

@admin.register(SupplyListing)
class SupplyListingAdmin(admin.ModelAdmin):
    list_display = ('commodity', 'quantity_kg', 'seller', 'status', 'auction_ends_at')
    list_filter = ('status', 'commodity')
    search_fields = ('seller__username', 'commodity__name')
    inlines = [BidInline]

@admin.register(Commodity)
class CommodityAdmin(admin.ModelAdmin):
    list_display = ('name', 'market_price', 'last_updated')

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('listing', 'buyer', 'final_price', 'created_at')