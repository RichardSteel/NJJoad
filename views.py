from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib import messages

from .models import Student, ArcheryEvent, JoadSession, JoadRoster, ArcherScore, InvoicePaid
from .forms import StudentForm, EventForm, AssignStudent, SessionForm, ArcherScoreForm, InvoiceForm

import re

# Create your views here.
@login_required
def pay_invoice(request):
    '''Method to accept payment for a session'''
    print(request)
    if request.method != 'POST':
        form = InvoiceForm()
    else:
        print("Posting payment")
        form = InvoiceForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('waxobejoad:index')
        else:
            print(form)
            print("Form is not valid")
    context = {'form': form}
    return render(request, 'waxobejoad/pay_invoice.html', context)

@login_required
def students(request):
    students = Student.objects.all().order_by('last_name').order_by('first_name')
    context = {'students': students}
    return render(request, 'waxobejoad/students.html', context)

def session_mgnt(request):
    return render(request, 'waxobejoad/session_mgnt.html')

def list_students(request):
    '''Method lists the students, which session they are enrolled in'''
    #Get active sessions
    sessions = JoadSession.objects.filter(sessionComplete=False)
    #Get rosters for active sessions
    rosters = JoadRoster.objects.filter(session__in=sessions)
    #Get students who are not in an active roster
    students = Student.objects.filter(active=True).exclude(joadroster__in=rosters).order_by('last_name').order_by('first_name')
    context = {'students': students}
    return render(request, 'waxobejoad/list_students.html', context)

@login_required
def sessions(request):
    #Get the session information. All active sessions and
    #  students registered for each session
    sessions = JoadSession.objects.filter(sessionComplete=False)
    rosters  = JoadRoster.objects.all()
    #rosters = JoadRoster.objects.all().order_by(student__last_name)
    context = {'sessions': sessions, 'rosters': rosters}
    return render(request, 'waxobejoad/sessions.html', context)    

@login_required
def assign_student(request):
    #Allow a coach to assign a student to a session.
    if request.method != 'POST':
        form = AssignStudent()
    else:
        form = AssignStudent(data=request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            #change the amount due
            #determine the correct amount due
            sessionLength = obj.session.durationOfSession
            #print(f"Session length in weeks is {sessionLength}")
            student = obj.student
            if not is_waxobe_member(obj.student):
                #print("Student is not a WaXoBe member")
                #Change amount due if not a member
                obj.amountDue = 20 * sessionLength
            else:
                #print("Student is a WaXoBe member")
                obj.amountDue = 15 * sessionLength
            #save with new amount due
            obj.save()
            #messages.success(request, 'Student successfully added to session')
            return redirect('waxobejoad:sessions')
        else:
            print("Assign student form is invalid")
            print(form)
    context = {'form': form}
    return render(request, 'waxobejoad/assign_students.html', context)

def is_waxobe_member(self):
    '''Simply returns if the student is a waxobe member or not'''
    #Return true if this student is a waxobe member
    return self.waxobe_member

def index(request):
    '''Start page'''
    context = {}
    rosterSignUp = []
    #if logged in, display any student assignment messages for students
    #belonging to this user.
    #Only if request.user is set - which is essentially the same as login_required.
    if request.user.is_authenticated:
        students = Student.objects.filter(parent=request.user)
        for student in students:
            roster = JoadRoster.objects.filter(student=student.id)
            if roster:
                rosterInfo = roster.get()
                rosterSignUp.append(rosterInfo)
        context = {'notes': rosterSignUp}
    return render(request, 'waxobejoad/index.html', context)

@login_required
def enter_score(request, student_id):
    #Allow a logged in staff user to enter student scores
    #Get student information
    student = Student.objects.get(id=student_id)
    #Get event information for drop down list
    events = ArcheryEvent.objects.filter(eventComplete=False)
    distance = 18
    target = 40
    context = {'student': student,
               'events': events,
               'distance' : distance, 
               'target': target}
    return render(request, 'waxobejoad/enter_score.html', context)

@login_required
def student(request, student_id):
    #Get the student information
    student = Student.objects.get(id=student_id)
    pinScore = student.pin_score
    #Get student scores and order by the date of the event
    scores = student.archerscore_set.all().order_by('event__dateOfEvent')
    context = {'student': student, 'scores': scores,
        'pin_score': pinScore, 'pin_range': range(pinScore)}
    return render(request, 'waxobejoad/student.html', context)

@login_required
def save_student_score(request):
    #print(f"Request is {request.method}")
    if request.method == 'POST':
        thisScoreForm = ArcherScoreForm(request.POST)
        if thisScoreForm.is_valid():
            print("Score is valid")
            #create object from model
            scoreDetail = ArcherScore()
            #and populate from the form
            student_id = thisScoreForm.cleaned_data["student"]
            print(f"Student is {student_id}")
            scoreDetail.student = Student.objects.get(id=student_id)
            event_id = thisScoreForm.cleaned_data["event"]
            scoreDetail.event = ArcheryEvent.objects.get(id=event_id)
            scoreDetail.distance = thisScoreForm.cleaned_data["distance"]
            scoreDetail.target = thisScoreForm.cleaned_data["target"]
            scoreDetail.score = thisScoreForm.cleaned_data["score"]
            #Save the score
            scoreDetail.save()
            #Then, calculate the students pin achievement score
            #This has to happen after the score is saved
            pinScore = calc_pin_score(student_id)
            print(f"Calculated pin score for student {student_id} is {pinScore}")
            #Then we need to update this pin_score into the student table
            Student.objects.filter(id=student_id).update(pin_score=pinScore)
            return redirect('waxobejoad:student', student_id=student_id)
    return render(request, 'waxobejoad/index.html')

def calc_pin_score(student_id):
    '''Method looks at all of the scores for the student and
    calculates their pin achievement value. This is returned as 
    an integer'''
    #Get all scores for the student in order of date.
    #Then fill pin 'buckets'. First try and fill the green pin, then purple.
    #Two shoots are required to achieve a pin.
    #Fill buckets relative to the current pin score.
    #So, if this is a new student, pin score is 0. Next pin is the green bucket
    #If this is an existing student with a pin score of 3, then the next pin
    #is White.
    #An asterix means any distance or target size.
    pinScores = {1: {'*/*': 50},
                 2: {'9/*': 100, '18/*': 30},
                 3: {'9/*': 150, '18/*': 50},
                 4: {'9/*': 200, '18/*': 100},
                 5: {'18/*': 150},
                 6: {'18/60': 200, '18/40': 190},
                 7: {'18/60': 250, '18/40': 240},
                 8: {'18/60': 270, '18/40': 260},
                 9: {'18/60': 285, '18/40': 280},
                 10: {'18/60': 290, '18/40': 285},
                 11: {'18/60': 295, '18/40': 290},
                }
    this_student = Student.objects.get(id=student_id)
    current_pin_score = this_student.pin_score
    start_pin = this_student.pin_score_start
    #Get shoots in order of date - date_added is when the score was added to
    #the database, not when the shoot was carried out.
    scores = ArcherScore.objects.filter(student=student_id).order_by('date_added')
    print(f"student is student ID {student_id}")
    print(f"Current pin score is {current_pin_score}")
    print(f"Starting pin value is {start_pin}")
    #We determine the new in score by;
    #Going through the shoots in date order.
    new_pin_value=1
    pinTarget = start_pin+new_pin_value
    for student_score in scores:
        #print(f"Score is {student_score}")
        thisScoreTarget = student_score.target
        thisScoreDistance = student_score.distance
        thisScoreScore = student_score.score
        print(f"Student scored {thisScoreScore} over {thisScoreDistance} at a {thisScoreTarget} target")
        pinAchieved = False
        a = pinScores[pinTarget]
        #print(f"Target for this student is {target}")
        #Each pin target can have one or more criteria - for different distances or target size
        for b in a:
            if pinAchieved:
                break
            c=int(a[b])
            print(f"The score to be achieved for this pin is {c}")
            #b is the distance and target size
            #c is the score required            
            #print(f"{c} = {b}")
            details = re.split(r"/", b)
            #print(details[0])
            #print(details[1])
            if details[1] == "*":
                print("The target size is irrelevent")
                print(f"Distance required {details[0]} and distance of shoot {thisScoreDistance}")
                if details[0] == "*":
                    print("The target distance is irrelevent")
                    if thisScoreScore >= c:
                        print(f"Student achieved pin {pinTarget}")
                        pinTarget+=1
                        pinAchieved = True
                        break
                    else:
                        print(f"Student did not achieve pin {pinTarget}")
                elif int(details[0]) == int(thisScoreDistance):
                    print(f"Compare student score {thisScoreScore} against {c}")
                    if int(thisScoreScore) >= c:
                        print(f"Student achieved pin {pinTarget}")
                        pinTarget+=1
                        pinAchieved = True
                        break
                    else:
                        print(f"Student did not achieve pin {pinTarget}. Needed {c} and scored {thisScoreScore}")
                else:
                    print("Target distance mismatch")                    
            elif int(details[1]) == int(thisScoreTarget):
                if details[0] == "*":
                    print("Distance is irrelevant")
                    if int(thisScoreScore) >= c:
                        print(f"Student achieved pin {pinTarget}")
                        pinTarget+=1
                        pinAchieved = True
                        break
                elif int(details[0]) == int(thisScoreDistance):
                    if int(thisScoreScore) >= c:
                        print(f"Student achieved pin {pinTarget}")
                        pinTarget+=1
                        pinAchieved = True
                        break
                    else:
                        print(f"Student did not achieve pin {pinTarget}. Needed {c} and scored {thisScoreScore}")
                else:
                    print("Target distance mismatch")
            else:
                print("Target size mismatch")

    #Get the shoot distance and target size.
    #From the pin start, determine what has to be achieved for pin start plus 1
    #Use target size and distance to find the score required
    #Current pin is always the pinTarget less 1
    return pinTarget-1

# @login_required
# def save_session_payment(request):
#     if request.method == 'POST':
#         form = InvoicePaid(data=request.POST)
#         if form.is_valid():
#             print("Invoice form is valid")
#             #create object from model
#             form.save()
#             return redirect('waxobejoad:pay_invoice')
#         else:
#             print("ERROR in invoice form")

#     return render(request, 'waxobejoad/index.html')

@login_required
def edit_student(request, student_id):
    #Allow a logged in user to edit student detils
    student = Student.objects.get(id=student_id)
    #Check that the logged user is the parent of this student
    if student.parent != request.user:
        raise Http404
    if request.method != 'POST':
        form = StudentForm(instance=student)
    else:
        form = StudentForm(instance=student, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('waxobejoad:student', student_id=student.id)
    context = {'student': student, 'form': form}
    return render(request, 'waxobejoad/edit_student.html', context)

@login_required
def new_event(request):
    if request.method != 'POST':
        #No data submitted. Create a blank form.
        form = EventForm()
    else:
        #This a POST method
        form = EventForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('waxobejoad:index')
    #This will run if request method is not a POST or the POST form is invalid
    context = {'form': form}
    return render(request, 'waxobejoad/new_event.html', context)

@login_required
def new_session(request):
    if request.method != 'POST':
        #No data submitted. Create a blank form.
        form = SessionForm()
    else:
        #This a POST method
        form = SessionForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('waxobejoad:index')
    #This will run if request method is not a POST or the POST form is invalid
    context = {'form': form}
    return render(request, 'waxobejoad/new_session.html', context)

@login_required
def new_student(request):
    #print(request)
    if request.method != 'POST':
        #No data submitted. Create a blank form.
        #print("new_student GET method")
        form = StudentForm()
    else:
        #This a POST method
        print("new_student POST method")
        form = StudentForm(request.POST)
        if form.is_valid():
            #Check, if waxobe member, then member ID is required
            print(form)
            member = form.cleaned_data.get('waxobe_member')
            print(f'Member {member}')
            if member == True:
                #Check we have a member ID
                member_id = form.cleaned_data.get('member_no')
                print(f'Member no {member_id}')
                if member_id == None:
                    raise Http404
            #Cannot save form until we associate the user with it.
            #Otherwise the db save will fail as owner is a foreign key
            new_student = form.save(commit=False)
            print(f"store student record against parent {request.user}")
            new_student.parent = request.user
            new_student.save()
            return redirect('waxobejoad:students')
        #else:
            #print("form is not valid - not saved")
    #This will run if request method is not a POST or the POST form is invalid
    context = {'form': form}
    return render(request, 'waxobejoad/new_student.html', context)



