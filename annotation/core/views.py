import ast
import json
import random
import re
from collections import defaultdict
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import F, Q, Sum, Func, Avg, Count
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from core.models import Prompt, Tag, EvaluationText, Annotation, Group, Profile
from markdown2 import markdown

# Batch examples into groupings of this size.
BATCH_SIZE = 10
# The desired number of annotations per example. Each example will be
# assigned to this many users before any new annotation gets assigned.
GOAL_NUM_ANNOTATIONS = 3


def _sanitize_username(username):
    # TODO(daphne): This should eventually get moved to a utils file.
    return re.sub(r'(.*)@.*', r'\1@*', username)


def onboard(request):
    if not request.user.is_authenticated:
        return redirect('/')

    return render(request, "onboard.html", {})


def splash(request):
    if request.user.is_authenticated:
        return redirect('/play')
    return render(request, "splash.html", {})


def join(request):
    if request.user.is_authenticated:
        return redirect('/play')
    return render(request, 'join.html')


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

    user = User.objects.get(username=username)
    counts = defaultdict(int)
    distances = []

    annotations_for_user = Annotation.objects.filter(
            annotator=user, attention_check=False)
    counts['points'] = annotations_for_user.aggregate(Sum('points'))['points__sum']
    counts['total'] = len(annotations_for_user)

    dist_from_boundary = annotations_for_user.annotate(
        distance=(Func(F('boundary') - F('text__boundary'), function='ABS')))
    counts['correct'] = len(dist_from_boundary.filter(distance=F('text__boundary')))

    distance = dist_from_boundary.aggregate(Avg('distance'))['distance__avg']

    # Check if the user has a profile object
    if Profile.objects.filter(user=user).exists():
        is_turker = Profile.objects.get(user=user).is_turker
    else:
        is_turker = False

    return render(request, 'profile.html', {
        'this_user': user,
        'is_turker': is_turker,
        'counts': counts,
        'distance': distance
    })


def annotate(request):
    if not request.user.is_authenticated:
        return redirect('/')

    # TODO(daphne): Optimize these into a single query.
    seen_set = Annotation.objects.filter(annotator=request.user).values('text')
    unseen_set = EvaluationText.objects.exclude(id__in=seen_set)

    # available_set should contain all examples that have between 1 and 3 annotations and
    # have not been seen before by this user.
    counts = Annotation.objects.values('text').annotate(count=Count('annotator'))
    available_set = counts.filter(count__gte=1,
                                  count__lte=GOAL_NUM_ANNOTATIONS,
                                  text_id__in=unseen_set).values('text')
    # If the available set is empty, then instead choose from all the examples in the
    # unseen set.
    if not available_set.exists():
        print('no available text!')
    available_set = unseen_set

    # TODO(daphne): We still need logic to handle the case where the user has
    # completed every available annotation. This code will crash in this case.

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
        text = random.choice(group.evaluation_texts.filter(id__in=available_set))
    else:
        text = random.choice(EvaluationText.objects.filter(id__in=available_set))

    prompt = text.prompt
    sentences = ast.literal_eval(text.body)[:10]

    # Check if the user has a profile object
    if Profile.objects.filter(user=request.user).exists():
        is_turker = Profile.objects.get(user=request.user).is_turker
    else:
        is_turker = False

    # The %age of all-human examples that will be converted to attention checks for turkers
    ATTENTION_CHECK_RATE = 0.5

    # Check attention if the user is from Mechanical Turk
    attention_check = False
    if is_turker and text.boundary == len(sentences):
        if random.random() < ATTENTION_CHECK_RATE:
            prompt.body += " Please choose 'It's all human-written so far.' for every sentence in this example."
            attention_check = True

    print("Here with text_id = {}".format(text.pk))
    return render(request, "annotate.html", {
        # "remaining": remaining,
        "prompt": prompt,
        "text_id": text.pk,
        "sentences": json.dumps(sentences),
        "name": request.user.username,
        "max_sentences": len(sentences),
        "boundary": text.boundary,
        "num_annotations": len(Annotation.objects.filter(annotator=request.user, attention_check=False)),
        "TAXONOMY": False,
        "annotation": annotation,  # Previous annotation given by user, else -1.
        "attention_check": int(attention_check)
    })


@csrf_exempt
def save(request):
    text = int(request.POST['text'])
    name = request.POST['name']
    boundary = int(request.POST['boundary'])
    revision = request.POST['revision']
    points = request.POST['points']
    attention_check = request.POST['attention_check']
    print(attention_check)

    grammar = request.POST['grammar'] == 'true'
    repetition = request.POST['repetition'] == 'true'
    entailment = request.POST['entailment'] == 'true'
    sense = request.POST['sense'] == 'true'

    annotation = Annotation.objects.create(
        annotator=request.user,
        text=EvaluationText.objects.get(pk=text),
        boundary=boundary,
        revision=revision,
        points=points,
        attention_check=attention_check
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
    username = request.POST['username']
    password = request.POST['password']
    user_source = request.POST['user_source']
    if User.objects.filter(username=username).exists():
        return redirect('/?signup_error=True')
    user = User.objects.create_user(
            username=username, email=None, password=password)
    profile = Profile.objects.create(
            user=user, is_turker=False, source=user_source)
    login(request, user)
    return redirect('/onboard')


def log_out(request):
    logout(request)
    return redirect('/')
