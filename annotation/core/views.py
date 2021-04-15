import re
import json
import random
from string import ascii_lowercase, digits
from collections import defaultdict
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import F, Q, Sum, Func, Avg, Count
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from markdown2 import markdown

from core.models import Prompt, Generation, Annotation, Playlist, Profile, SEP, FeedbackOption


# Batch examples into groupings of this size.
BATCH_SIZE = 10
# The desired number of annotations per example. Each example will be
# assigned to this many users before any new annotation gets assigned.
GOAL_NUM_ANNOTATIONS = 3

# helper function taken from (https://gist.github.com/jcinis/2866253)
def generate_random_username(length=16, chars=ascii_lowercase+digits, split=4, delimiter='-'):
    username = ''.join(random.choice(chars) for i in range(length + 1))

    if split:
        username = delimiter.join([username[start:start+split] for start in range(0, len(username), split)])

    try:
        User.objects.get(username=username)
        return generate_random_username(length=length, chars=chars, split=split, delimiter=delimiter)
    except User.DoesNotExist:
        return username;

def _sanitize_username(username):
    # TODO(daphne): This should eventually get moved to a utils file.
    return re.sub(r'(.*)@.*', r'\1@*', username)

def str_to_list(text):
    return text.split(SEP)

def onboard(request):
    if not request.user.is_authenticated:
        # Note: This should be the *only* time where the user is not authenticated
        # TODO: save annotations to session and prompt to save after X annotations
        user = User.objects.create(username=generate_random_username())
        profile = Profile.objects.create(user=user, is_temporary=True)
        login(request, user)

    return render(request, "onboard.html", {
        'profile': Profile.objects.get(user=request.user)
    })


def splash(request):
    return render(request, "splash.html")


def join(request):
    return render(request, 'join.html')


def play(request):
    playlists = Playlist.objects.all()
    enum_playlists = enumerate(playlists)
    total_available = sum(len(playlist.generations.all()) for playlist in playlists)
    for playlist in playlists:
        playlist.description = markdown(playlist.description)
        playlist.details = markdown(playlist.details)

    return render(request, 'play.html', {
        'playlists': playlists,
        'enum_playlists': enum_playlists,
        'total': total_available,
        'profile': Profile.objects.get(user=request.user)
    })


def leaderboard(request):
    # slow, should be an offline job instead of re-computing on page request
    users = [user.id for user in User.objects.all() if not Profile.objects.get(user=user).is_temporary]
    top_users = User.objects.filter(pk__in=users).annotate(points=Sum(F('annotation__points'))).order_by('-points')
    username_point_pairs = [
        (_sanitize_username(u.username), u.points)
        for u in top_users if u.points and u.has_usable_password()]

    return render(request, 'leaderboard.html', {
        'sorted_usernames': tuple(username_point_pairs),
        'profile': Profile.objects.get(user=request.user)
    })


def profile(request, username):
    user = User.objects.get(username=username)
    counts = {}

    # GENERAL DATA
    general_counts = defaultdict(int)
    annotations_for_user = Annotation.objects.filter(
            annotator=user, attention_check=False)
    general_counts['points'] = annotations_for_user.aggregate(Sum('points'))['points__sum']
    general_counts['total'] = len(annotations_for_user)

    # boundary is 0 indexed starting from "continuation of text"
    # prompt__num_sentences is a 1-indexed count, starting from first prompt sentence.
    general_counts['correct'] = len(annotations_for_user.filter(boundary=F('generation__prompt__num_sentences')-1))
    general_counts['past_boundary'] = len(annotations_for_user.filter(boundary__gte=F('generation__prompt__num_sentences')))

    dist_from_boundary = annotations_for_user.annotate(
        distance=((F('boundary') + 1 - F('generation__prompt__num_sentences'))))
    general_counts['avg_distance'] = dist_from_boundary.aggregate(Avg('distance'))['distance__avg'] # negative means avg is before correct boundary
    counts['general'] = general_counts

    for id, name in enumerate(['reddit', 'nyt', 'speeches', 'recipes'],1):
        print(id)
        playlist_counts = defaultdict(int)
        playlist_annotations_for_user = Annotation.objects.filter(
                annotator=user, attention_check=False, playlist=id)
        playlist_counts['points'] = playlist_annotations_for_user.aggregate(Sum('points'))['points__sum']
        playlist_counts['total'] = len(playlist_annotations_for_user)

        playlist_counts['correct'] = len(playlist_annotations_for_user.filter(boundary=F('generation__prompt__num_sentences')-1))
        playlist_counts['past_boundary'] = len(playlist_annotations_for_user.filter(boundary__gte=F('generation__prompt__num_sentences')))

        playlist_dist_from_boundary = playlist_annotations_for_user.annotate(
            distance=((F('boundary') + 1 - F('generation__prompt__num_sentences'))))
        playlist_counts['avg_distance'] = playlist_dist_from_boundary.aggregate(Avg('distance'))['distance__avg'] # negative means avg is before correct boundary
        print(name + " COUNTS: ", playlist_counts)
        counts[name] = playlist_counts

    print("BIG COUNT: \n", counts)

    # Check if the user has a profile object
    if Profile.objects.filter(user=user).exists():
        is_turker = Profile.objects.get(user=user).is_turker
    else:
        is_turker = False

    trophies = []

    if counts['general']['total'] > 0:
        trophies.append({'emoji': '🤖', 'description': 'Complete one annotation.'})
    if counts['general']['points'] and counts['general']['points'] > 50:
        trophies.append({'emoji': '✨', 'description': 'Acheive 50 points.'})
    if counts['general']['correct'] and counts['general']['correct'] > 0:
        trophies.append({'emoji': '🔎', 'description': 'Correctly identify one boundary.'})

    return render(request, 'profile.html', {
        'profile': Profile.objects.get(user=request.user),
        'this_user': user,
        'is_turker': is_turker,
        'counts': counts,
        'trophies': trophies
    })


def annotate(request):
    # TODO(daphne): Optimize these into a single qucery.
    seen_set = Annotation.objects.filter(annotator=request.user).values('generation')
    unseen_set = Generation.objects.exclude(id__in=seen_set)

    # counts should contain all examples that have between 1 and 3 annotations and
    # have not been seen before by this user.
    playlist, generations = None, None
    counts = Annotation.objects.values('generation').annotate(count=Count('annotator'))
    available_generations = counts.filter(count__gte=1, count__lte=GOAL_NUM_ANNOTATIONS, generation__in=unseen_set).values('generation')

    # Mark only examples in the correct playlist (if one was specified) as available.
    playlist_id = int(request.GET.get('playlist', -1))
    if playlist_id >= 0:
        playlist = Playlist.objects.get(id=playlist_id)
        generations = playlist.generations.filter(id__in=available_generations)
        print("Annotating playlist = {}.".format(playlist))

    # If the available set is empty, then instead choose from all the examples in the
    # unseen set.
    if not generations or not generations.exists():
        print('no available text!')
        generations = playlist.generations.filter(id__in=unseen_set) if playlist else unseen_set
    # TODO(daphne): We still need logic to handle the case where the user has
    # completed every available annotation. This code will crash in this case.

    annotation = -1  # If this one hasn't been annotated yet.
    if 'qid' in request.GET:
        qid = int(request.GET['qid'])
        # playlist_id = -1
        print("In annotate with qid = {}.".format(qid))
        generation = Generation.objects.get(pk=qid)
        if seen_set.filter(generation=qid).exists():
          print('User has already annotated example with qid = {}'.format(qid))
          annotation = Annotation.objects.filter(annotator=request.user, generation_id=qid)[0].boundary
    else:
        # TODO(daphne): We do eventually need logic here to handle when all annotations
        # for a playlist have been completed. This code will still fail in this case.
        generation = random.choice(generations)

    prompt_sentences = str_to_list(generation.prompt.body)
    generated_sentences = str_to_list(generation.body)
    continuation_sentences = prompt_sentences[1:] + generated_sentences

    # For some datasets, most importntly recipes, the first sentence of the prompt might
    # have new lines in it which are critical to understanding.
    prompt_sentences[0] = prompt_sentences[0].replace("\n", "<br/>")

    # Check if the user has a profile object
    if Profile.objects.filter(user=request.user).exists():
        is_turker = Profile.objects.get(user=request.user).is_turker
    else:
        is_turker = False

    # The percentage of all-human examples that will be converted to attention checks for turkers
    ATTENTION_CHECK_RATE = 0.5

    # Check attention if the user is from Mechanical Turk
    attention_check = False
    if (
        is_turker
        and generation.boundary == len(generated_sentences)
        and random.random() < ATTENTION_CHECK_RATE
    ):
        prompt.body += " Please choose 'It's all human-written so far.' for every sentence in this example."
        attention_check = True

    print("Here with generation_id = {}".format(generation.pk))

    fluency_reasons  = FeedbackOption.objects.filter(is_default=True, category="fluency")
    substance_reasons = FeedbackOption.objects.filter(is_default=True, category="substance")

    return render(request, "annotate.html", {
        # "remaining": remaining,
        'profile': Profile.objects.get(user=request.user),
        "prompt": prompt_sentences[0],
        "text_id": generation.pk,
        "sentences": json.dumps(continuation_sentences[:9]),
        "name": request.user.username,
        "max_sentences": len(continuation_sentences[:9]),
        "boundary": generation.boundary,
        "annotation": annotation,  # Previous annotation given by user, else -1.
        "attention_check": int(attention_check),
        "playlist": playlist_id,
        "fluency_reasons": fluency_reasons,
        "substance_reasons": substance_reasons
    })


@csrf_exempt
def save(request):
    text = int(request.POST['text'])
    name = request.POST['name']
    playlist_id = request.POST['playlist_id']
    print("Playlist id in save: ", playlist_id)

    boundary = int(request.POST['boundary'])
    points = request.POST['points']
    attention_check = request.POST['attention_check']

    annotation = Annotation.objects.create(
        annotator=request.user,
        generation=Generation.objects.get(pk=text),
        playlist = playlist_id,
        boundary=boundary,
        points=points,
        attention_check=attention_check
    )

    feedback_options  = [v[0] for v in FeedbackOption.objects.filter(is_default=True).values_list("shortname")]
    for option in feedback_options:
        if request.POST[option] == 'true':
            annotation.reason.add(FeedbackOption.objects.get(shortname=option))

    other_reason = request.POST['other_reason']
    if other_reason:
        new_reason = FeedbackOption.objects.create(shortname = str(hash(other_reason)), category = "other", description = other_reason, is_default = False)
        annotation.reason.add(new_reason)

    remaining = request.session.get('remaining', BATCH_SIZE)
    request.session['remaining'] = remaining - 1

    annotation.save()

    return JsonResponse({'status': 200})


def log_in(request):
    if request.method == 'GET':
        return render(request, 'join.html')

    username, password = request.POST['username'], request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('/onboard')
    else:
        return redirect('/join?login_error=True')


def sign_up(request):
    username = request.POST['username']
    password = request.POST['password']
    user_source = request.POST['user_source']

    if User.objects.filter(username=username).exists():
        return redirect('/join?signup_error=True')

    user = User.objects.create_user(username=username, email=None, password=password)
    profile = Profile.objects.create(user=user, source=user_source)

    login(request, user)
    return redirect('/onboard')


def log_out(request):
    logout(request)
    return redirect('/')
