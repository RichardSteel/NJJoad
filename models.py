from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.fields import DurationField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

# Create your models here.
class Student(models.Model):
    '''Class to hold student information'''
    #Only 2 forms of archery are stored or taught
    archery_style= (
        ('R', 'Recurve'),
        ('C', 'Compound'),
    )
    student_sex   = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    start_time_pref = (
        ('A', '3:30pm'),
        ('B', '4:30pm'),
        ('N', 'No Preference'),
    )
    #parent = models.ForeignKey(User, on_delete=CASCADE)
    first_name    = models.CharField(max_length=30)
    last_name     = models.CharField(max_length=30)
    #Each student has to have a parent as the foreign key
    parent        = models.ForeignKey(User, on_delete=CASCADE)
    date_of_birth = models.DateField()
    preference    = models.CharField(max_length=1,
        choices=start_time_pref, default='N')
    style         = models.CharField(max_length=1,
        choices=archery_style,
        default='R')
    sex           = models.CharField(_("Sex"), max_length=1, default='M', choices=student_sex)
    student_email = models.EmailField(max_length=100)
    waxobe_member = models.BooleanField(
        help_text='Are you a full member, in good standing, of the club?')
    #Membership number is blank if not a member
    member_no     = models.PositiveIntegerField(null=True, blank=True,
        help_text='Your unique WaXoBe club membership ID.')
    date_added    = models.DateTimeField(auto_now_add=True)
    active        = models.BooleanField(default=True)
    #Following fields are no editable - they do not show up on the form
    #Only can be set by the admin or by the program.
    pin_score     = models.SmallIntegerField(null=False, editable=False, default=0)
    #This will be used to set a starting position for a student
    #pin_score will be calculated based on the scores in the database.
    #If we are missing past scores the student has achieved, the pin_score_start
    #can account for this. 
    pin_score_start = models.SmallIntegerField(null=True, editable=False)

    def __str__(self):
        #Check if student is assigned to a session
        assigned = JoadRoster.objects.filter(student=self.id)
        if assigned:
            #Indicates that the student is assigned
            return f"{self.first_name} {self.last_name}"
        else:
            if self.active:
                return f"{self.first_name} {self.last_name} [{self.preference}]"
            else:
                #Indicates that the student is inactive
                return f"({self.first_name} {self.last_name})"

class ArcherComment(models.Model):
    '''Class to hold student comments. These are comments the coaches make about students'''
    student       = models.ForeignKey(Student, on_delete=CASCADE)
    coach         = models.ForeignKey(User, on_delete=CASCADE)
    comment       = models.TextField(max_length=200)
    date_added    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{date_added} : {comment}"

class JoadSession(models.Model):
    '''Defines the properties of a JOAD session'''
    startDate = models.DateField(_('Date of session start'))
    sessionName = models.CharField(_('Name of session') ,max_length=32)
    durationOfSession = models.PositiveIntegerField(_('Length of session, in weeks'))
    sessionComplete = models.BooleanField(default=False, help_text='Set this true when the session is completed.')
    sessionFull = models.BooleanField(default=False, help_text='Set this true when the session is full.')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"WaXoBe JOAD session: {self.sessionName} start date: {self.startDate}"

class JoadRoster(models.Model):
    '''Defines the students enrolled in a session'''
    student = models.ForeignKey(Student, on_delete=CASCADE)
    session = models.ForeignKey(JoadSession, on_delete=CASCADE)
    amountDue = models.PositiveIntegerField(_('Cost of the session'), default=150)

    def __str__(self):
        return f"Amount due for {self.student} for session {self.session} is => ${self.amountDue}"

class InvoicePaid(models.Model):
    '''Class will hold details of the amount paid for the session'''
    roster = models.ForeignKey(JoadRoster, help_text='The student registration to pay', on_delete=CASCADE)
    #roster has the session key and the student key.
    #This links a student to a session
    amountPaid = models.PositiveIntegerField()
    paidInFull = models.BooleanField(_('Check if this invoice is complete'), default=False)
    comments = models.TextField(max_length=200, null=True, blank=True, help_text='Coach comments about this payment')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        #Get the student and session information
        r = self.roster
        this_student = r.student
        this_session = r.session
        return f"{self.amountPaid} paid for student {this_student} for {this_session}"

class ArcheryEvent(models.Model):
    '''will hold the details of an archery shoot'''
    dateOfEvent = models.DateField(_('Date of shoot'))
    location = models.CharField(_('Shoot location'), max_length=30)
    eventType = models.CharField(_('Type of shoot'), max_length=30)
    eventComplete = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.eventType} at {self.location} on {self.dateOfEvent}"

class ArcherScore(models.Model):
    '''will hold the result of an event'''
    student = models.ForeignKey(Student, on_delete=CASCADE)
    event = models.ForeignKey(ArcheryEvent, on_delete=CASCADE)
    distance = models.IntegerField(default="18")
    target = models.IntegerField(default="40")
    score = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} scored {self.score} at {self.event}"

    def get_shoot_date(self):
        return self.event.dateOfEvent

    def get_event_type(self):
        return self.event.eventType

