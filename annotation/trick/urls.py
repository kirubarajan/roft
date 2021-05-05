"""trick URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from core.views import (
    annotate,
    about,
    help,
    leaderboard,
    save,
    join,
    log_in,
    log_out,
    sign_up,
    profile,
    play
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('profile/<str:username>/', profile, name='profile'),
    path('annotate/', annotate, name="annotate"),
    path('leaderboard/', leaderboard, name="leaderboard"),
    path('save/', save, name="save"),
    path('login/', log_in, name='log_in'),
    path('join/', join, name='join'),
    path('signup/', sign_up, name='sign_up'),
    path('logout/', log_out, name="log_out"),
    path('help/', help, name="help"),
    path('about/', about, name="about"),
    path('', play, name="play")
]
