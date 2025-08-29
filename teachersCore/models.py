from django.db import models
from datetime import timedelta
from django.utils import timezone

from django.contrib.auth.models import AbstractUser,Group,Permission,BaseUserManager
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role="teacher", **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # force  role=admin on createsuperuser
        return self.create_user(username, email, password, role="admin", **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    role = models.CharField(choices=ROLE_CHOICES,max_length=10,default='teacher')
    email = models.EmailField(unique=True,blank=True, null=True) 
    '''
    When subclassing AbstractUser, you need to override groups and 
    user_permissions fields with related_name so they don’t clash with the default auth.User
    '''
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_set", 
        blank=True
    )
    objects=UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})" 
    
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    staff_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    subject = models.CharField(max_length=100, blank=True, null=True)
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('onLeave', 'On Leave'),
        ('inactive', 'Inactive'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    duty_eligibility = models.BooleanField(default=True)
    last_assigned_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.staff_id})"

class DutyPeriod(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()


    def __str__(self):
        return f"Duty Period {self.start_date} - {self.end_date}"
    
# class DutyAssignment(models.Model):
#     duty_period = models.ForeignKey(DutyPeriod, on_delete=models.CASCADE, related_name="assignments")
#     teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="assignments")


#     def __str__(self):
#         return f"{self.teacher} assigned for {self.duty_period}"

class DutyAssignment(models.Model):
    duty_period = models.ForeignKey("DutyPeriod", on_delete=models.CASCADE)
    teacher = models.ForeignKey("Teacher", on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=6)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.teacher} assigned from {self.start_date} to {self.end_date}"



class Attendance(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="attendance")
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return f"{self.teacher} ({self.check_in} - {self.check_out})"

