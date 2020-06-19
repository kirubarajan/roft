import ast
import json
import random
from collections import defaultdict
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from core.models import Prompt, Tag, EvaluationText, Annotation


def leaderboard(request):
    points = defaultdict(int)
    for annotation in Annotation.objects.filter():
        points[annotation.annotator.username] += annotation.points
    sorted_usernames = sorted(points.items(), key=lambda x: x[1], reverse=True)
    print(sorted_usernames)
    return render(request, 'leaderboard.html', {'sorted_usernames': tuple(sorted_usernames)})


def profile(request, username):
    if not request.user.is_authenticated:
        return redirect('/')
    profile = User.objects.get(username=username)
    counts = defaultdict(int)
    distances = []
    for annotation in Annotation.objects.filter(annotator=profile):
        counts['points'] += annotation.points
        counts['total'] += 1
        distances.append(abs(annotation.boundary - annotation.text.boundary))
        if annotation.boundary == annotation.text.boundary:
            counts['correct'] += 1
    return render(request, 'profile.html', {
        'profile': profile, 
        'counts': counts, 
        'distance': sum(distances) / len(distances)
    })


def onboard(request):
    if request.user.is_authenticated:
        return redirect('/profile/' + request.user.username)
    return render(request, "onboard.html", {})


def annotate(request):
    seen = Annotation.objects.filter(annotator=request.user).values('text')
    text = random.choice(EvaluationText.objects.exclude(id__in=seen))
    sentences = ast.literal_eval(text.body)
    args = {
        "prompt": text.prompt, 
        "text_id": text.pk, 
        "sentences": json.dumps(sentences), 
        "name": request.user.username, 
        "max_sentences": len(sentences),
        "boundary": text.boundary,
        "TAXONOMY": False
    }
    
    return render(request, "annotate.html", args)


@csrf_exempt
def save(request):  
    text = int(request.POST['text'])
    name = request.POST['name']
    boundary = int(request.POST['boundary'])
    revision = request.POST['revision']
    points = request.POST['points']

    grammar = request.POST['grammar'] == 'true'
    repetition = request.POST['repetition'] == 'true'
    entailment = request.POST['entailment'] == 'true'
    sense = request.POST['sense'] == 'true'

    annotation = Annotation.objects.create(
        annotator=request.user,
        text=EvaluationText.objects.get(pk=text),
        boundary=boundary,
        revision=revision,
        points=points
    )

    if grammar: annotation.tags.add(Tag.objects.get(name="grammar"))
    if repetition: annotation.tags.add(Tag.objects.get(name="repetition"))
    if entailment: annotation.tags.add(Tag.objects.get(name="entailment"))
    if sense: annotation.tags.add(Tag.objects.get(name="sense"))
    annotation.save()

    return JsonResponse({'status': 200})


def log_in(request):
    if request.method == 'GET': return render(request, 'signin.html', {})
    username, password = request.POST['username'], request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('/')
    else:
        return redirect('/?login_error=True')


def sign_up(request):
    email, username, password = request.POST['email'], request.POST['username'], request.POST['password']
    if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
        return redirect('/?signup_error=True') 
    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    return redirect('/annotate')


def log_out(request):
    logout(request)
    return redirect('/')
