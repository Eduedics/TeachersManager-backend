from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Teacher,Attendance,DutyAssignment,DutyPeriod
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['username']=user.username
        # ...

        return token
    def validate(self, attrs):
        # attrs already contains 'username' and 'password'
        data = super().validate(attrs)
        data.update({
            "role": self.user.role,
            "username": self.user.username,
        })
        return data
    
class TeacherSerializer(ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    class Meta:
        model=Teacher
        fields=['id', 'username', 'email', 'staff_id', 'department', 
            'subject', 'status', 'duty_eligibility', 'last_assigned_at', 'user']
        extra_kwargs={
            'user':{"write_only":True}
        }

class AttendanceSerializer(ModelSerializer):
    class Meta:
        model=Attendance
        fields="__all__"

class DutyPeriodSerializer(ModelSerializer):
    class Meta:
        model= DutyPeriod
        fields= "__all__"
    
class DutyAssignmentSerializer(ModelSerializer):
    duty_period=DutyPeriodSerializer(read_only=True)
    duty_period_id= serializers.PrimaryKeyRelatedField(queryset=DutyPeriod.objects.all(),source="duty_period",write_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all(),source='teacher',write_only=True)
    teacher = TeacherSerializer(read_only=True)
    class Meta:
        model=DutyAssignment
        fields = ["id", "duty_period", "duty_period_id", "teacher_id", "teacher", "start_date", "end_date"]
