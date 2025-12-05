from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health-check'),
    # Auth & profile
    path('users/', views.UserCreateView.as_view(), name='user-create'),
    path('auth/login/', views.custom_token_auth, name='custom-token-auth'),
    path('me/profile/', views.UserProfileView.as_view(), name='user-profile'),

    # Listings
    path('listings/', views.ListingListView.as_view(), name='listing-list'),
    path('listings/create/', views.ListingCreateView.as_view(), name='listing-create'),
    path('listings/<int:pk>/', views.ListingDetailView.as_view(), name='listing-detail'),
    path('listings/<int:pk>/update/', views.ListingUpdateView.as_view(), name='listing-update'),

    # Bids
    path('bids/', views.BidCreateView.as_view(), name='bid-create'),

    # Commodities
    path('commodities/', views.CommodityListCreateView.as_view(), name='commodity-list-create'),
    
    # 🧠 AI-POWERED ENDPOINTS
    # Market Intelligence
    path('ai/market-analytics/', views.MarketAnalyticsView.as_view(), name='market-analytics'),
    path('ai/market-insights/', views.ai_market_insights, name='ai-market-insights'),
    
    # AI Recommendations
    path('ai/recommendations/', views.AIRecommendationsView.as_view(), name='ai-recommendations'),
    
    # Smart Bidding
    path('ai/bid-suggestions/<int:listing_id>/', views.ai_bid_suggestions, name='ai-bid-suggestions'),
    path('ai/competitor-analysis/<int:listing_id>/', views.ai_competitor_analysis, name='ai-competitor-analysis'),
    
    # AI Analysis
    path('ai/analyze/<int:listing_id>/', views.trigger_ai_analysis, name='trigger-ai-analysis'),
    
    # Notifications
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark-notification-read'),
]
