from django.shortcuts import render

from .serializers import MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from.models import Teacher,Attendance,DutyAssignment,DutyPeriod
from teachersCore import permissions
from . serializers import TeacherSerializer,AttendanceSerializer,DutyAssignmentSerializer,DutyPeriodSerializer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta





User = get_user_model()

from django.utils import timezone


# import random

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.db.models import Sum, F, ExpressionWrapper, DurationField
from datetime import datetime, timedelta

class LoginView(TokenObtainPairView):
    serializer_class= MyTokenObtainPairSerializer

class RefreshTokenView(TokenRefreshView):
    pass

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    return Response({'message':'Successfully logged out'})

@api_view(["GET"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def ListTeachers(request):
    teachers = Teacher.objects.all()
    serializer=TeacherSerializer(teachers,many=True)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def Create_teacher(request):
    print("Received data:", request.data)  # Debug what's received
    
    user_data = request.data.get("user")
    teacher_data = request.data.get("teacher")
    
    print("User data:", user_data)
    print("Teacher data:", teacher_data)
    
    if not user_data or not teacher_data:
        return Response({"error": "User and Teacher data required"}, status=400)
    
    try:
        # Creating user manually
        user = User.objects.create_user(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            role="teacher"
        )
        print("User created:", user.id)
        teacher_data["user"] = user.id
        print("Teacher data with user ID:", teacher_data)
        
        serializer = TeacherSerializer(data=teacher_data)
        print("Serializer data:", serializer.initial_data)
        
        if serializer.is_valid():
            print("Serializer is valid")
            teacher = serializer.save()
            print("Teacher created:", teacher.id)
            return Response(serializer.data, status=201)
        else:
            print("Serializer errors:", serializer.errors)
            user.delete()
            return Response(serializer.errors, status=400)
            
    except Exception as e:
        print("Error occurred:", str(e))
        # If any error occurs, clean up
        if 'user' in locals():
            user.delete()
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def GetTeacher(request,pk):
    try:
        teacher= Teacher.objects.get(pk=pk)
    except Teacher.DoesNotExist:
        return Response({'error':'Teacher not found'},status=status.HTTP_404_NOT_FOUND)
    serializer = TeacherSerializer(teacher)
    return Response(serializer.data)

@api_view(["PUT","PATCH"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def Update_teacher(request,pk):
    try:
        teacher = Teacher.objects.get(pk=pk)
    except Teacher.DoesNotExist:
        return Response({'error':'Teacher not found'},status=status.HTTP_404_NOT_FOUND)
    serializer =TeacherSerializer(teacher,data=request.data,partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data,status=status.HTTP_200_OK)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def Delete_teacher(request,pk):
    try:
        teacher=Teacher.objects.get(pk=pk)
    except Teacher.DoesNotExist:
        return Response({'error':'Teacher not found'},status=status.HTTP_404_NOT_FOUND)
    teacher.delete()
    return Response({'message':"Teacher Deleted"},status= status.HTTP_204_NO_CONTENT)


# attendance views
@api_view(["POST"])
@permission_classes([IsAuthenticated, permissions.IsTeacher])
def Check_in(request):
    # Check if the authenticated user has a teacher_profile
    if not hasattr(request.user, 'teacher_profile'):
        return Response({"error": "User is not associated with a teacher profile."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        teacher = request.user.teacher_profile
        attendance = Attendance.objects.create(teacher=teacher, check_in=timezone.now())
        return Response({'message': "Checked in", 'id': attendance.id})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(["POST"])
@permission_classes([IsAuthenticated, permissions.IsTeacher])
def Check_out(request):
    print('user', request.user)
    
    # Check if the authenticated user has a teacher_profile
    if not hasattr(request.user, 'teacher_profile'):
        return Response({"error": "User is not associated with a teacher profile."}, status=status.HTTP_400_BAD_REQUEST)
    
    teacher = request.user.teacher_profile
    
    try:
        attendance = Attendance.objects.filter(
            teacher=teacher, 
            check_out__isnull=True
        ).latest('check_in')
    except Attendance.DoesNotExist:
        return Response({"error": "No active session found"}, status=status.HTTP_404_NOT_FOUND)
    if timezone.now() < attendance.check_in:
        return Response({"error": "Checkout time cannot be before checkin time"}, status=status.HTTP_400_BAD_REQUEST)
    
    attendance.check_out = timezone.now()
    attendance.save()

    duration = attendance.check_out - attendance.check_in
    hours = duration.total_seconds() / 3600
    
    return Response({
        "message": "Checked out successfully",
        "id": attendance.id,
        "check_in": attendance.check_in,
        "check_out": attendance.check_out,
        "duration_hours": round(hours, 2)
    })
@api_view(["GET"])
@permission_classes([IsAuthenticated, permissions.IsTeacher])
def My_attendance(request):
    teacher=request.user.teacher_profile
    records=Attendance.objects.filter(teacher=teacher)
    serializer= AttendanceSerializer(records, many=True)
    return Response(serializer.data)

# DutyPeriod crud
@api_view(["GET"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def List_duty_periods(request):
    periods=DutyPeriod.objects.all()
    serializer = DutyPeriodSerializer(periods,many=True)
    return Response(serializer.data)
@api_view(["POST"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def Create_duty_period(request):
    serializer=DutyPeriodSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

'''
Filter eligible teachers (duty_eligibility=True and status="active").
Sort by last_assigned_at → the teacher who was assigned longest ago gets priority.
Pick randomly among those who haven’t been assigned recently (to avoid strict rotation).
Update last_assigned_at when a teacher is chosen.
'''
# @api_view(["POST"])
# @permission_classes([IsAuthenticated, permissions.IsAdmin])
# def Assign_duty(request,period_id):
#     period = get_object_or_404(DutyPeriod, id=period_id)

#     teachers = Teacher.objects.filter(
#         duty_eligibility=True,
#         status='active'
#     ).order_by('last_assigned_at')

#     if not teachers.exists():
#         return Response(
#             {"error": "No eligible teachers"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     chosen_teacher = teachers.first()

#     assignment = DutyAssignment.objects.create(
#         duty_period=period,
#         teacher=chosen_teacher
#     )
#     chosen_teacher.last_assigned_at = timezone.now()
#     chosen_teacher.save()

#     serializer = DutyAssignmentSerializer(assignment)
#     return Response({"success": True, "assignment": serializer.data}, status=status.HTTP_201_CREATED)

@api_view(["POST"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def Assign_duty(request, period_id):
    period = get_object_or_404(DutyPeriod, id=period_id)
    today = timezone.now().date()
    last_duty = DutyAssignment.objects.order_by("-end_date").first()

    if last_duty and last_duty.end_date >= today:
        start_date = last_duty.end_date + timezone.timedelta(days=1)
    else:
        start_date = today

    end_date = start_date + timezone.timedelta(days=7)
    teachers = Teacher.objects.filter(
        duty_eligibility=True,
        status="active"
    ).order_by("last_assigned_at")

    if not teachers.exists():
        return Response(
            {"error": "No eligible teachers"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if last_duty:
        teacher_list = list(teachers)
        try:
            last_index = teacher_list.index(last_duty.teacher)
            next_index = (last_index + 1) % len(teacher_list)
            chosen_teacher = teacher_list[next_index]
        except ValueError:
            chosen_teacher = teachers.first()
    else:
        chosen_teacher = teachers.first()
    assignment = DutyAssignment.objects.create(
        duty_period=period,
        teacher=chosen_teacher,
        start_date=start_date,
        end_date=end_date
    )
    print('choosen_teacher',chosen_teacher)

    chosen_teacher.last_assigned_at = timezone.now()
    chosen_teacher.save()

    serializer = DutyAssignmentSerializer(assignment)
    return Response(
        {
            "success": True,
            "assignment": serializer.data,
            "message": f"{chosen_teacher} scheduled for duty "
                       f"({start_date} - {end_date})"
        },
        status=status.HTTP_201_CREATED,
    )
    # try:
    #     # period=DutyPeriod.objects.all()
    #     period = get_object_or_404(DutyPeriod, id=period_id)
    # except DutyPeriod.DoesNotExist:
    #     return Response({"error":"Duty period not found"},status=status.HTTP_404_NOT_FOUND)
    # teachers = Teacher.objects.filter(duty_eligibility=True,status='active').order_by('last_assigned_at')
    # if not teachers.exists():
    #     return Response({"error": "No eligible teachers"}, status=status.HTTP_400_BAD_REQUEST)
    # choosen_teacher=teachers.first()
    # assignment = DutyAssignment.objects.create(duty_period=period,teacher=choosen_teacher)
    # choosen_teacher.last_assigned_at=timezone.now()
    # choosen_teacher.save()
    # serializer = DutyAssignmentSerializer(assignment)
    # return Response(serializer.data,status=status.HTTP_201_CREATED)
# view all assignments
@api_view(["GET"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def List_assignments(request):
    assignments= DutyAssignment.objects.all()
    serializer = DutyAssignmentSerializer(assignments,many=True)
    return Response(serializer.data)
# individual teacher assignmet
@api_view(["GET"])
@permission_classes([IsAuthenticated, permissions.IsTeacher])
def My_duty(request):
    teacher= request.user.teacher_profile
    assignment = DutyAssignment.objects.filter(teacher=teacher)
    serializer = DutyAssignmentSerializer(assignment,many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def WeeklyReport(request,teacher_id):
    start_date_str = request.query_params.get("start_date")
    end_date_str=request.query_params.get("end_date")
    if not start_date_str or not end_date_str:
        return Response({"error":"start_date and end_date required"},status=status.HTTP_400_BAD_REQUEST)
    
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    try:
        teacher = Teacher.objects.get(pk=teacher_id)
    except:
        return Response({"error":"Teacher not found"},status=status.HTTP_404_NOT_FOUND)
    
    '''
    getting attendance record
    '''
    record= Attendance.objects.filter(
        teacher=teacher,
        check_in__date__gte = start_date.date(),
        check_in__date__lte = end_date.date(),
        check_out__isnull=False
    ).annotate(
        duration=ExpressionWrapper(
            F("check_out")-F("check_in"),
            output_field=DurationField()
        )
    )
    total_time = sum([r.duration for r in record],timedelta())
    total_hours = round(total_time.total_seconds()/3600,2)

    # pdf creation
    response =HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] =f'attachment;filename="report_{teacher.staff_id}_{start_date.date()}_{end_date.date()}.pdf"'

    p= canvas.Canvas(response)
    p.setFont('Helvetica-Bold',16)
    p.drawString(100,800,"Teachers weekly Attendance Report")

    p.setFont('Helvetica-Bold',12)
    p.drawString(100,770,f"Teacher:{teacher.user.username} ({teacher.staff_id})")
    p.drawString(100,750,f"Week : {start_date.date()} => {end_date.date()}")
    p.drawString(100,730,f"Total Hours:{total_hours}")

    y=700
    p.setFont("Helvetica-Bold",12)
    p.drawString(100,y,"Check In")
    p.drawString(250,y,"Check Out")
    p.drawString(400,y,"Duration")
    p.setFont("Helvetica",12)

    for r in record:
        y -= 20
        p.drawString(100, y, r.check_in.strftime("%Y-%m-%d %H:%M:%S"))
        p.drawString(250, y, r.check_out.strftime("%Y-%m-%d %H:%M:%S"))
        hours, remainder = divmod(r.duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        p.drawString(400, y, duration_str)
    
    p.showPage()
    p.save()
    return response
@api_view(["POST"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def Generate_duty_roster(request, period_id):
    """
    exaple of api call await api.post("duties/roster/1/", { weeks: 12 });
    Auto-generate duty roster for the next X weeks.
    Example payload: { "weeks": 12 } -> generates 12 weeks (~3 months) schedule
    """
    period = get_object_or_404(DutyPeriod, id=period_id)
    weeks = request.data.get("weeks", 12)  # default 12 weeks (~3 months)

    today = timezone.now().date()
    last_duty = DutyAssignment.objects.order_by("-end_date").first()

    if last_duty and last_duty.end_date >= today:
        start_date = last_duty.end_date + timezone.timedelta(days=1)
    else:
        start_date = today

    teachers = Teacher.objects.filter(
        duty_eligibility=True,
        status="active"
    ).order_by("last_assigned_at")

    if not teachers.exists():
        return Response(
            {"error": "No eligible teachers"},
            status=status.HTTP_400_BAD_REQUEST
        )

    teacher_list = list(teachers)
    roster = []
    if last_duty:
        try:
            last_index = teacher_list.index(last_duty.teacher)
            next_index = (last_index + 1) % len(teacher_list)
        except ValueError:
            next_index = 0
    else:
        next_index = 0

    for i in range(weeks):
        end_date = start_date + timezone.timedelta(days=7)
        chosen_teacher = teacher_list[next_index]

        assignment = DutyAssignment.objects.create(
            duty_period=period,
            teacher=chosen_teacher,
            start_date=start_date,
            end_date=end_date
        )

        chosen_teacher.last_assigned_at = timezone.now()
        chosen_teacher.save()

        roster.append(DutyAssignmentSerializer(assignment).data)
        next_index = (next_index + 1) % len(teacher_list)
        start_date = end_date + timezone.timedelta(days=1)

    return Response(
        {
            "success": True,
            "message": f"Duty roster generated for {weeks} weeks",
            "assignments": roster
        },
        status=status.HTTP_201_CREATED
    )
