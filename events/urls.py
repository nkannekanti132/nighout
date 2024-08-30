from django.urls import path
from . import views

urlpatterns = [
    path('events/create/', views.create_event, name='create_event'),
    path('events/<int:event_id>/invite/', views.invite_to_event, name='invite_to_event'),
    path('events/<int:event_id>/rsvp/', views.rsvp_for_event, name='rsvp_for_event'),
    path('events/<int:event_id>/attendees/', views.view_event_attendees, name='view_event_attendees'),
    path('events/<int:event_id>/send-message/', views.send_message_to_event, name='send_message_to_event'),
    path('events/my-created/', views.get_created_events, name='get_created_events'),
    path('events/my-collaborations/', views.get_collaborator_events, name='get_collaborator_events'),
    path('events/<int:event_id>/invitations/', views.view_invitations_by_status, name='view_invitations_by_status'),
    path('events/<int:event_id>/messages/', views.get_event_messages, name='get_event_messages'),
    path('events/<int:event_id>/edit/', views.edit_event, name='edit_event'),
]
