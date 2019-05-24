"""woodenwheel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from isp_semi_auto.views import index, gradebook_upload, \
    subject_teachers, subjects, isp_options, attendance_options, assignments, \
    students, fill_out_isp

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name="index"),
    path('upload_gradebook/', gradebook_upload, name="gradebook"),
    path('get_teachers/', subject_teachers, name="get-teachers"),
    path('get_subjects/', subjects, name="get-subjects"),
    path('get_isp_options/', isp_options, name="get-isp-options"),
    path('get_attendance_options/', attendance_options, name="get-attendance-options"),
    path('get_assignments/', assignments, name="get-assignments"),
    path('get_students/', students, name="get-students"),
    path('fill_out_isp/', fill_out_isp, name="fill-out-isp"),

]
