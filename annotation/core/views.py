import ast
import json
import random
import re
from collections import defaultdict
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import F, Sum, Func, Avg
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from core.models import Prompt, Tag, EvaluationText, Annotation, Group
from markdown2 import markdown

BATCH_SIZE = 10


def _sanitize_username(username):
    # TODO(daphne): This should eventually get moved to a utils file.
    return re.sub(r'(.*)@.*', r'\1@*', username)


def play(request):
    if not request.user.is_authenticated:
        return redirect('/')
        
    groups = Group.objects.all()
    total_available = sum(len(g.evaluation_texts.all()) for g in groups)

    for group in groups:
        group.description = markdown(group.description)

    return render(request, 'play.html', {
        'groups': groups,
        'total': total_available
    })


def leaderboard(request):
    points = defaultdict(int)

    top_users = User.objects.filter().annotate(
        points=Sum(F('annotation__points'))).order_by('-points')
    username_point_pairs = [
        (_sanitize_username(u.username), u.points)
        for u in top_users if u.points]

    return render(request, 'leaderboard.html', {
        'sorted_usernames': tuple(username_point_pairs)
    })


def profile(request, username):
    if not request.user.is_authenticated:
        return redirect('/')

    profile = User.objects.get(username=username)
    counts = defaultdict(int)
    distances = []

    annotations_for_user = Annotation.objects.filter(annotator=profile)
    counts['points'] = annotations_for_user.aggregate(Sum('points'))['points__sum']
    counts['total'] = len(annotations_for_user)
    
    dist_from_boundary = annotations_for_user.annotate(
        distance=(Func(F('boundary') - F('text__boundary'), function='ABS')))
    counts['correct'] = len(dist_from_boundary.filter(distance=F('text__boundary')))

    distance = dist_from_boundary.aggregate(Avg('distance'))['distance__avg']

    return render(request, 'profile.html', {
        'profile': profile, 
        'counts': counts, 
        'distance': distance
    })


def onboard(request):
    if not request.user.is_authenticated:
        return redirect('/')
        
    return render(request, "onboard.html", {})


def splash(request):
    if request.user.is_authenticated:
        return redirect('/play')
    return render(request, "splash.html", {})


def annotate(request):
    if not request.user.is_authenticated:
        return redirect('/')

    seen_set = Annotation.objects.filter(annotator=request.user).values('text')
  
    annotation = -1  # If this one hasn't been annotated yet.
    if 'qid' in request.GET:
        qid = int(request.GET['qid']) 
        print("In annotate with qid = {}.".format(qid))
        text = EvaluationText.objects.get(pk=qid)
        if seen_set.filter(text=qid).exists():
          print('User has already annotated example with qid = {}'.format(qid))
          annotation = Annotation.objects.filter(annotator=request.user, text_id=qid)[0].boundary
    elif 'group' in request.GET:
        group = Group.objects.get(id=int(request.GET['group']))
        print("In annotate with group = {}.".format(group))
        text = random.choice(group.evaluation_texts.exclude(id__in=seen_set))
    else:
        text = random.choice(EvaluationText.objects.exclude(id__in=seen_set))
    
    sentences = ast.literal_eval(text.body)[:10]
    # remaining = request.session.get('remaining', BATCH_SIZE)
    
    print("Here with text_id = {}".format(text.pk))
    return render(request, "annotate.html", {
        # "remaining": remaining,
        "prompt": text.prompt, 
        "text_id": text.pk, 
        "sentences": json.dumps(sentences), 
        "name": request.user.username, 
        "max_sentences": len(sentences),
        "boundary": text.boundary,
        "num_annotations": len(Annotation.objects.filter(annotator=request.user)),
        "TAXONOMY": False,
        "annotation": annotation,  # Previous annotation given by user, else -1. 
    })


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
    
    remaining = request.session.get('remaining', BATCH_SIZE)
    request.session['remaining'] = remaining - 1

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
    username, password = request.POST['username'], request.POST['password']
    if User.objects.filter(username=username).exists():
        return redirect('/?signup_error=True') 
    user = User.objects.create_user(username=username, email=None, password=password)
    login(request, user)
    return redirect('/onboard')


def log_out(request):
    logout(request)
    return redirect('/')
