from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location']

class InvitationForm(forms.Form):
    email = forms.EmailField()

class RSVPForm(forms.Form):
    status = forms.ChoiceField(choices=[('Accepted', 'Accept'), ('Rejected', 'Reject'),('Pending','Pending')])
