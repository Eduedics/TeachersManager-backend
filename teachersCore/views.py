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
    user_data = request.data.get("user")
    teacher_data = request.data.get("teacher")
    if not user_data or not teacher_data:
        return Response({"error": "User and Teacher data required"}, status=400)
    # manual user creation so as only Admin can create  a teacher teacher only logs in
    user = User.objects.create_user(username=user_data["username"],email=user_data["email"],password=user_data["password"],role="teacher")
    # serialize teacher dats with linked user
    teacher_data["user"] = user.id
    serializer = TeacherSerializer(data=teacher_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    else:
        user.delete()  # rollback user if teacher fails
        return Response(serializer.errors, status=400)


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
    teacher= request.user.teacher_profile
    attenadance = Attendance.objects.create(teacher=teacher,check_in=timezone.now())
    return Response({'message':"Checked in",'id':attenadance.id})
@api_view(["POST"])
@permission_classes([IsAuthenticated, permissions.IsTeacher])
def Check_out(request,pk):
    teacher=request.user.teacher_profile
    try:
        attendance = Attendance.objects.get(pk=pk,teacher=teacher,check_out__isnull=True)
    except Attendance.DoesNotExist:
        return Response({"error": "No active session found"}, status=status.HTTP_404_NOT_FOUND)
    attendance.check_out =timezone.now()
    attendance.save()
    return Response({"message":"check out","id":attendance.id})
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
@api_view(["POST"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def Assign_duty(request,period_id):
    try:
        period=DutyPeriod.objects.all()
    except DutyPeriod.DoesNotExist:
        return Response({"error":"Duty period not found"},status=status.HTTP_404_NOT_FOUND)
    teachers = Teacher.objects.filter(duty_eligibility=True,status='active').order_by('last_assigned_at')
    if not teachers.exists():
        return Response({"error": "No eligible teachers"}, status=status.HTTP_400_BAD_REQUEST)
    choosen_teacher=teachers.first()
    assignment = DutyAssignment.objects.create(duty_period=period,teacher=choosen_teacher)
    choosen_teacher.last_assigned_at=timezone.now()
    choosen_teacher.save()
    serializer = DutyAssignmentSerializer(assignment)
    return Response(serializer.data,status=status.HTTP_201_CREATED)
# view all assignments
@api_view(["GET"])
@permission_classes([IsAuthenticated, permissions.IsAdmin])
def List_assignments(request):
    assignments= DutyAssignment.objects.all()
    serializer = DutyAssignmentSerializer(assignments)
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
    
    start_date = datetime.fromisofformat(start_date_str)
    end_date = datetime.fromisofformat(end_date_str)

    try:
        teacher = Teacher.objects.get(pk=teacher_id)
    except:
        return Response({"error":"Teacher not found"},status=status.HTTP_404_NOT_FOUND)
    
    '''
    getting attendance record
    '''
    record= Attendance.objects.filter(
        teacher=teacher,
        Check_in__date__gte = start_date.date(),
        Check_in__date__lte = end_date.date(),
        Check_out__isnull=False
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
        y-=20
        p.drawString(100,y,str(r.check_in))
        p.drawString(250,y,str(r.check_out))
        p.drawString(400,y,str(r.duration))
    
    p.showPage()
    p.save()
    return response