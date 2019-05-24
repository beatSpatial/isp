from django.contrib import admin

# Django admin cookbook
# https://books.agiliq.com/projects/django-admin-cookbook/en/latest/

# Register your models here.
from .models import Student, Teacher, Assignment, Gradebook,\
    StudentAssignmentGrades, Subject, SubjectTemplate


class StudentAssignmentGradesAdmin(admin.ModelAdmin):
    search_fields = (
        'student__lastname',
        'student__firstname',
    )


class StudentAdmin(admin.ModelAdmin):
    search_fields = (
        'fyid',
        'lastname',
        'firstname',
    )


class TeacherAdmin(admin.ModelAdmin):
    search_fields = (
        'lastname',
        'firstname',
    )

    def subject_display(self, obj):
        return ", ".join([
            str(subject) for subject in obj.subjects.all()
        ])
    subject_display.short_description = "Subjects"

    list_display = ['lastname', 'firstname', 'subject_display', ]


class SubjectTemplateAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'step', 'stage']
    ordering = ['subject_name', 'step', 'flavour']


admin.site.register(Student, StudentAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Subject)
admin.site.register(SubjectTemplate, SubjectTemplateAdmin)
admin.site.register(Assignment)
admin.site.register(Gradebook)
admin.site.register(StudentAssignmentGrades, StudentAssignmentGradesAdmin)
