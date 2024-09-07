from django.db import models
from django.utils import timezone
import os

def case_image_path(instance, filename):
    return f'case_images/{instance.case.caseid}/{filename}'

def evidence_image_path(instance, filename):
    return f'evidence/{instance.case.caseid}/{filename}'

def officer_image_path(instance, filename):
    return f'officers/{instance.id}/{filename}'

def suspect_image_path(instance, filename):
    return f'suspects/{instance.case.caseid}/{instance.suspect_id}/{filename}'

def victim_image_path(instance, filename):
    return f'victims/{instance.case.caseid}/{instance.victim_id}/{filename}'

def public_report_attachment_path(instance, filename):
    return f'public_reports/{instance.user.NIN_id}/{instance.report_id}/{filename}'

class Authorized(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.TextField()
    last_logged_in = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=255)

class CaseReport(models.Model):
    caseid = models.CharField(max_length=50, primary_key=True)
    caseno = models.IntegerField()
    case_date = models.DateField()
    nature_of_case = models.CharField(max_length=255)
    case_description = models.TextField(blank=True)
    lat = models.FloatField()
    lng = models.FloatField()
    recorded_date = models.DateTimeField(default=timezone.now)
    casestatus = models.CharField(max_length=20, default='ongoing')

class CaseImage(models.Model):
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=case_image_path)
    description = models.CharField(max_length=255, blank=True)

class CaseTimeline(models.Model):
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE, related_name='timeline')
    date = models.DateTimeField()
    activity = models.CharField(max_length=255)

class Evidence(models.Model):
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE, related_name='evidence')
    image = models.ImageField(upload_to=evidence_image_path, null=True, blank=True)
    description = models.TextField(blank=True)
    name = models.CharField(max_length=255)

class Message(models.Model):
    date = models.DateField()
    time = models.TimeField()
    message = models.TextField()
    username = models.CharField(max_length=255)

class NatureOfCase(models.Model):
    nature_of_case = models.CharField(max_length=50, primary_key=True)
    case_count = models.IntegerField(default=0)

class OfficerRecord(models.Model):
    name = models.TextField()
    image = models.ImageField(upload_to=officer_image_path)
    joined_date = models.DateField()
    email = models.EmailField()
    contact = models.CharField(max_length=255)

class OfficerArchive(models.Model):
    officer = models.OneToOneField(OfficerRecord, on_delete=models.CASCADE)
    left_date = models.DateField()

class OfficerAndCase(models.Model):
    officer = models.ForeignKey(OfficerRecord, on_delete=models.CASCADE)
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    enrollment = models.CharField(max_length=255)
    case_assigned_on = models.DateField(null=True, blank=True)
    case_left_on = models.DateField(null=True, blank=True)

class PDFReport(models.Model):
    file = models.FileField(upload_to='pdf_reports/')
    username = models.CharField(max_length=255)
    file_name = models.TextField()

class Suspect(models.Model):
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE, related_name='suspects')
    suspect_id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, blank=True)
    contact = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    statement = models.TextField(blank=True)
    image = models.ImageField(upload_to=suspect_image_path, null=True, blank=True)

class Victim(models.Model):
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE, related_name='victims')
    victim_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    contact = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    statement = models.TextField(blank=True)
    image = models.ImageField(upload_to=victim_image_path, null=True, blank=True)

class Tactic(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    video_url = models.CharField(max_length=255, blank=True)

class PublicUser(models.Model):
    NIN_id = models.BigIntegerField(primary_key=True)
    Name = models.CharField(max_length=255)
    Contact_no = models.CharField(max_length=20)
    Password = models.TextField()

class AdminPosted(models.Model):
    message_id = models.AutoField(primary_key=True)
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE)
    message = models.TextField()
    time_stamp = models.DateTimeField(default=timezone.now)

class PublicResponse(models.Model):
    user = models.ForeignKey(PublicUser, on_delete=models.CASCADE)
    admin_message = models.ForeignKey(AdminPosted, on_delete=models.CASCADE)
    message = models.TextField()
    time_stamp = models.DateTimeField(default=timezone.now)

class PublicReport(models.Model):
    user = models.ForeignKey(PublicUser, on_delete=models.CASCADE)
    report_id = models.AutoField(primary_key=True)
    report_message = models.TextField()
    time_stamp = models.DateTimeField(default=timezone.now)
    attachment = models.FileField(upload_to=public_report_attachment_path, null=True, blank=True)