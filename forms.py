from django import forms
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from .models import Student, ArcheryEvent, JoadSession, JoadRoster, InvoicePaid

class ArcherScoreForm(forms.Form):
    student  = forms.IntegerField()
    event    = forms.IntegerField()
    distance = forms.IntegerField()
    target   = forms.IntegerField()
    score    = forms.IntegerField()

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'sex',
            'style',
            'preference',
            'student_email',
            'waxobe_member',
            'member_no',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(format='%d/%m/%Y', attrs={'style': 'width:12em', 'type': 'date'}),
            'first_name': forms.TextInput(attrs={'style': 'width:25em'}),
            'last_name': forms.TextInput(attrs={'style': 'width:25em'}),
            'sex': forms.Select(attrs={'style': 'width:6em'}),
            'style': forms.Select(attrs={'style': 'width:8em'}),
            'preference': forms.Select(attrs={'style': 'width:12em'}),
            'student_email': forms.TextInput(attrs={'style': 'width:30em'}),
            'member_no': forms.TextInput(attrs={'style': 'width:5em'}),
            }
        
class EventForm(forms.ModelForm):
    class Meta:
        model = ArcheryEvent
        fields = [
            'dateOfEvent',
            'location',
            'eventType',
        ]
        labels = {
            'eventType': "Shoot type (nationals, state, local JOAD 300, etc)"
        }
        widgets = {
            'dateOfEvent': forms.DateInput(format='%d/%m/%Y', attrs={'style': 'width:300px', 'type': 'date'}),
            'location': forms.TextInput(attrs={'style': 'width:500px'}),
            'eventType': forms.TextInput(attrs={'style': 'width:400px'}),
            }

class SessionForm(forms.ModelForm):
    class Meta:
        model = JoadSession
        fields = [
            'startDate',
            'sessionName',
            'durationOfSession',
        ]

class AssignStudent(forms.ModelForm):
    #Need to limit assignment to sessions which are not complete and 
    #Also limit to students who are active.
    def __init__(self, *args, **kwargs):
        super(AssignStudent, self).__init__(*args, **kwargs)
        self.fields['session'].queryset = JoadSession.objects.filter(sessionComplete=False,sessionFull=False)
        self.fields['student'].queryset = Student.objects.filter(active=True)

    class Meta:
        model = JoadRoster
        fields = ['session', 'student']

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = InvoicePaid
        fields = ['roster', 'amountPaid', 'paidInFull', 'comments']
        labels = { 'roster': _('Student Invoice'),
                   'amountPaid': _('Amount Paid'),
                }
        widgets = {'comments': forms.Textarea(attrs={'cols': 80, 'rows': 5})}
        
    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        invpaid = InvoicePaid.objects.filter(paidInFull=True)
        self.fields['roster'].queryset = JoadRoster.objects.exclude(invoicepaid__in=invpaid)

