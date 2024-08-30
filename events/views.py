from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Event, Invitation, User, Message
from .forms import EventForm, InvitationForm, RSVPForm
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.mail import send_mail
from nightout import settings
from django.http import HttpResponseForbidden


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_event(request):
    try:
        data = json.loads(request.body)
        form = EventForm(data)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            return JsonResponse({'status': 'success', 'event_id': event.id})
        else:
            print("Form errors:", form.errors)  # Debug: Print form errors
            return JsonResponse({'errors': form.errors.as_json()}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def invite_to_event(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        data = json.loads(request.body)
        form = InvitationForm(data)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                invitation = Invitation.objects.create(event=event, user=user)
                
                # Send email notification
                subject = 'You Have Been Invited to an Event!'
                message = f'Hello {user.username},\n\nYou have been invited to the event "{event.title}" by {request.user.username}. Please check your account for more details.'
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [email]

                send_mail(subject, message, from_email, recipient_list)

                return JsonResponse({'status': 'success'})
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
        else:
            return JsonResponse({'errors': form.errors.as_json()}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def rsvp_for_event(request, event_id):
    data = json.loads(request.body)
    form = RSVPForm(data)
    
    if form.is_valid():
        status = form.cleaned_data['status']
        event = get_object_or_404(Event, id=event_id)
        
        invitation, created = Invitation.objects.get_or_create(event=event, user=request.user)
        
        if created or invitation.status is "Pending":  # New or no previous response
            invitation.status = status
            invitation.save()
            
            # Send notification to the event organizer
            subject = 'RSVP Status Updated'
            message = (f'Hello {event.organizer.username},\n\n'
                       f'{request.user.username} has updated their RSVP status to "{status}" for your event "{event.title}".\n\n'
                       'Please check the event details for more information.')
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [event.organizer.email]

            send_mail(subject, message, from_email, recipient_list)

            return JsonResponse({'status': 'success', 'rsvp_status': status})
        else:
            return JsonResponse({'error': 'Already responded'}, status=400)
    
    return JsonResponse({'error': 'Invalid data'}, status=400)

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def view_invitations_by_status(request, event_id):
    print(request.GET.get('status'))
    status = request.GET.get('status')
    if status not in [None, 'Accepted', 'Rejected', 'Pending']:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    event = get_object_or_404(Event, id=event_id)
    invitations = Invitation.objects.filter(event=event)
    
    if status:
        invitations = invitations.filter(status=status)
    
    invitation_list = [{
        'user': invitation.user.email,
        'status': invitation.status
    } for invitation in invitations]
    
    return JsonResponse({'invitations': invitation_list})



@csrf_exempt
@login_required
@require_http_methods(["GET"])
def view_event_attendees(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    invitations = Invitation.objects.filter(event=event).select_related('user')
    attendees = [{'email': invitation.user.email, 'first_name': invitation.user.first_name, 'last_name': invitation.user.last_name} for invitation in invitations]
    return JsonResponse({'attendees': attendees})

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_message_to_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    data = json.loads(request.body)
    message_content = data.get('message')
    if message_content:
        # Save the message to the database
        Message.objects.create(
            event=event,
            user=request.user,
            content=message_content
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'No message provided'}, status=400)

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def get_created_events(request):
    events = Event.objects.filter(organizer=request.user).values()
    return JsonResponse({'events': list(events)})

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def get_collaborator_events(request):
    events = Event.objects.filter(invitations__user=request.user).values()
    return JsonResponse({'events': list(events)})


@login_required
@require_http_methods(["GET"])
def get_event_messages(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    messages = event.messages.all().order_by('-timestamp')  # Fetch messages for the event
    messages_list = [
        {
            'user': message.user.email,
            'content': message.content,
            'timestamp': message.timestamp.isoformat()
        }
        for message in messages
    ]
    return JsonResponse({'messages': messages_list})


@csrf_exempt
@login_required
def edit_event(request, event_id):
    # Fetch the event, ensure it exists, and belongs to the requesting user (organizer)
    event = get_object_or_404(Event, id=event_id)

    # Check if the logged-in user is the organizer of the event
    if event.organizer != request.user:
        return HttpResponseForbidden(JsonResponse({'error': 'You are not allowed to edit this event.'}, status=403))

    if request.method == 'PUT':  # Using PUT for editing/updating the resource
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Updating event details with the JSON data
        title = data.get('title', event.title)
        description = data.get('description', event.description)
        date = data.get('date', event.date)
        location = data.get('location', event.location)

        # Ensure all required fields are present
        if not title or not description or not date or not location:
            return JsonResponse({'error': 'All fields (title, description, date, location) are required.'}, status=400)

        # Updating the event
        event.title = title
        event.description = description
        event.date = date
        event.location = location
        event.save()

        # Return updated event data as JSON
        return JsonResponse({
            'message': 'Event updated successfully',
            'event': {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'date': event.date,
                'location': event.location,
                'organizer': event.organizer.email,
            }
        }, status=200)

    return JsonResponse({'error': 'Invalid request method. Only PUT is allowed.'}, status=405)

