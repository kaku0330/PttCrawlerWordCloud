from django.contrib import admin
from django.urls import path
from django.conf.urls import url

from ptt import views as ptt

urlpatterns = [
    # path('home', views.home),
    # path('getdata', views.getdata),

    url(r'^$', ptt.index),
    url(r'^getdata/$', ptt.getdata),
    url(r'^crawler/$',ptt.crawler),
    url(r'^test/$',ptt.test),
]
