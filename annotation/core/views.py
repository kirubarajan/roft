import re
import json
import random
from string import ascii_lowercase, digits
from datetime import datetime, time
from collections import defaultdict
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import F, Q, Sum, Func, Avg, Count
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import ValidationError, validate_password, password_validators_help_text_html
from markdown2 import markdown

from core.models import Prompt, Generation, Annotation, Playlist, Profile, SEP, FeedbackOption, Timestamp


# Batch examples into groupings of this size.
BATCH_SIZE = 10
# The desired number of annotations per example. Each example will be
# assigned to this many users before any new annotation gets assigned.
GOAL_NUM_ANNOTATIONS = 3
# The playlist version to show in the UI
_PLAYLIST_VERSION = "0.4"


# The cached leaderboard.
cached_leaderboard = None
leaderboard_cache_time = None

# helper function taken from (https://gist.github.com/jcinis/2866253)


def generate_random_username(
        length=16,
        chars=ascii_lowercase +
        digits,
        split=4,
        delimiter='-'):
    username = ''.join(random.choice(chars) for i in range(length + 1))

    if split:
        username = delimiter.join([username[start:start + split]
                                  for start in range(0, len(username), split)])

    try:
        User.objects.get(username=username)
        return generate_random_username(
            length=length,
            chars=chars,
            split=split,
            delimiter=delimiter)
    except User.DoesNotExist:
        return username


def _sanitize_username(username):
    # TODO(daphne): This should eventually get moved to a utils file.
    return re.sub(r'(.*)@.*', r'\1@*', username)


def str_to_list(text):
    return text.split(SEP)


def _is_temp(user):
    """Returns true if the specified user is a temporary, non-real one."""
    return Profile.objects.get(user=user).is_temporary


def _build_counts_dict(user, playlist_name=None, attention_check=False):
    """Returns stats about the specified user's performance on the spacified playlist."""
    # Query for the data on annotations for the given playlist id
    if playlist_name:
        # find all annotations in the correct playlist.
        playlists = Playlist.objects.filter(shortname=playlist_name, version=_PLAYLIST_VERSION)
        generations_in_playlist = Generation.objects.filter(playlist__shortname=playlist_name)
        annotations = Annotation.objects.filter(generation__in=generations_in_playlist)
    else:
        annotations = Annotation.objects
      

    user_annotations = annotations.filter(
        annotator=user,
        attention_check=attention_check,
    )

    # Calculate the average distance from boundary from the annotations
    dist_from_boundary = user_annotations.annotate(
        distance=((F('boundary') + 1 - F('generation__prompt__num_sentences'))))

    # Fill in the dictionary with the appropriate values
    counts = defaultdict(int)
    counts['points'] = user_annotations.aggregate(Sum('points'))['points__sum']
    counts['total'] = len(user_annotations)
    counts['correct'] = len(user_annotations.filter(
        boundary=F('generation__prompt__num_sentences') - 1))
    counts['past_boundary'] = len(user_annotations.filter(
        boundary__gte=F('generation__prompt__num_sentences')))
    counts['avg_distance'] = dist_from_boundary.aggregate(Avg('distance'))['distance__avg']

    return counts


def help(request):
    return render(request, "help.html", {
        'profile': Profile.objects.get(user=request.user)
    })


def about(request):
    return render(request, "about.html", {
        'profile': Profile.objects.get(user=request.user)
    })


def join(request):
    if request.user.is_authenticated:
        if not _is_temp(request.user):
            return redirect('/play')

        return render(request, 'join.html', {
            'profile': Profile.objects.get(user=request.user)
        })

    return render(request, 'join.html')


def play(request):
    if not request.user.is_authenticated:
        # TODO: save annotations to session and prompt to save after X
        # annotations
        unseen_set = Generation.objects.all()
        user = User.objects.create(username=generate_random_username())
        profile = Profile.objects.create(user=user, is_temporary=True)
        login(request, user)

    playlists = Playlist.objects.filter(version=_PLAYLIST_VERSION)
    total_available = sum(len(playlist.generations.all()) for playlist in playlists)
    for playlist in playlists:
        playlist.description = markdown(playlist.description)
        playlist.details = markdown(playlist.details)

    return render(request, 'play.html', {
        'playlists': playlists,
        'total': total_available,
        'profile': Profile.objects.get(user=request.user)
    })


def _leaderboard_is_stale():
    current_time = datetime.now()
    if leaderboard_cache_time:
        elapsed_time = current_time - leaderboard_cache_time
        elapsed_minutes = divmod(elapsed_time.total_seconds(), 60)
        return elapsed_minutes > 15
    else:
        return True


def leaderboard(request):
    if _leaderboard_is_stale():
        profiles_with_points = Profile.objects.filter(is_temporary=False)
        profiles_with_points = profiles_with_points.annotate(
            points=Sum(F('user__annotation__points')))
        top_profiles = profiles_with_points.filter(points__gt=0)
        # Only include profiles of valid, signed in users. This line is equivalent
        # to checking that has_usable_password  is set to True for each user.
        top_profiles = top_profiles.filter(Q(user__is_active=True) &
                                           Q(user__password__isnull=False) &
                                           ~Q(user__password__startswith='!'))
        top_profiles = top_profiles.order_by('-points')[:50]
        cached_leaderboard = [
            (_sanitize_username(p.user.username), p.points) for p in top_profiles]
        leaderboard_cache_time = datetime.now()

    request_user_rank = -1
    for rank, (user, score) in enumerate(cached_leaderboard):
        if user == request.user:
            request_user_rank = rank + 1
            break

    # TODO(daphne): Decide whether or not `request_user` should be sanitized.
    show_user = request.user.is_authenticated and not _is_temp(request.user)
    profile = Profile.objects.get(user=request.user)

    return render(request, 'leaderboard.html', {
        'sorted_usernames': tuple(cached_leaderboard),
        'request_user': request.user.username if show_user else "",
        'request_user_rank': request_user_rank,
        'profile': profile
    })


def profile(request, username):
    if not request.user.is_authenticated:
        return redirect('/')

    user = User.objects.get(username=username)
    counts = {}

    # GENERAL DATA
    counts['general'] = _build_counts_dict(user)
    counts['reddit'] = _build_counts_dict(user, "Short Stories")
    counts['nyt'] = _build_counts_dict(user, "New York Times")
    counts['speeches'] = _build_counts_dict(user, "Presidential Speeches")
    counts['recipes'] = _build_counts_dict(user, "Recipes")

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
    if not request.user.is_authenticated:
        return redirect('/login')

    # TODO(daphne): Optimize these into a single qucery.
    seen_set = Annotation.objects.filter(
        annotator=request.user).values('generation')
    unseen_set = Generation.objects.exclude(id__in=seen_set)

    # counts should contain all examples that have between 1 and 3 annotations and
    # have not been seen before by this user.
    playlist, generations = None, None
    counts = Annotation.objects.values('generation').annotate(count=Count('annotator'))
    available_generations = counts.filter(
        count__gte=1,
        count__lte=GOAL_NUM_ANNOTATIONS,
        generation__in=unseen_set).values('generation')

    # Mark only examples in the correct playlist (if one was specified) as
    # available.
    playlist_id = int(request.GET.get('playlist', -1))
    if playlist_id >= 0:
        playlist = Playlist.objects.get(id=playlist_id)
        generations = playlist.generations.filter(id__in=available_generations)
        print("Annotating playlist = {}.".format(playlist))

    # If the available set is empty, then instead choose from all the examples in the
    # unseen set.
    if not generations or not generations.exists():
        print('no available text!')
        generations = playlist.generations.filter(
            id__in=unseen_set) if playlist else unseen_set
    # TODO(daphne): We still need logic to handle the case where the user has
    # completed every available annotation. This code will crash in this case.

    annotation = -1  # If this one hasn't been annotated yet.
    if 'qid' in request.GET:
        qid = int(request.GET['qid'])
        # playlist_id = -1
        print("In annotate with qid = {}.".format(qid))
        generation = Generation.objects.get(pk=qid)
        if request.user.is_authenticated and seen_set.filter(
                generation=qid).exists():
            print('User has already annotated example with qid = {}'.format(qid))
            annotation = Annotation.objects.filter(
                annotator=request.user, generation_id=qid)[0].boundary
    else:
        # TODO(daphne): We do eventually need logic here to handle when all annotations
        # for a playlist have been completed. This code will still fail in this
        # case.
        generation = random.choice(generations)
    
    print(generation.prompt)

    prompt_sentences = str_to_list(generation.prompt.body)
    print("Prompt Sentences:")
    print(prompt_sentences)
    generated_sentences = str_to_list(generation.body)
    print("Gen Sentences:")
    print(generated_sentences)
    continuation_sentences = prompt_sentences[1:] + generated_sentences

    # For some datasets, most importntly recipes, the first sentence of the prompt might
    # have new lines in it which are critical to understanding.
    prompt_sentences[0] = prompt_sentences[0].replace("\n", "<br/>")

    # Check if the user has a profile object
    if request.user.is_authenticated and Profile.objects.filter(user=request.user).exists():
        is_turker = Profile.objects.get(user=request.user).is_turker
    else:
        is_turker = False

    # The percentage of all-human examples that will be converted to attention
    # checks for turkers
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

    fluency_reasons = FeedbackOption.objects.filter(is_default=True, category="fluency")
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
        "annotation": annotation,# Previous annotation given by user, else -1.
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
        playlist=playlist_id,
        boundary=boundary,
        points=points,
        attention_check=attention_check
    )

    for timestamp in request.POST['timestamps'].split(','):
        Timestamp.objects.create(
            annotation=annotation,
            date=datetime.fromtimestamp(int(timestamp) / 1000)
        )

    feedback_options = [
        v[0] for v in FeedbackOption.objects.filter(is_default=True).values_list("shortname")]
    for option in feedback_options:
        if request.POST[option] == 'true':
            annotation.reason.add(FeedbackOption.objects.get(shortname=option))

    other_reason = request.POST['other_reason']
    if other_reason:
        new_reason = FeedbackOption.objects.create(
            shortname=str(
                hash(other_reason)),
            category="other",
            description=other_reason,
            is_default=False)
        annotation.reason.add(new_reason)

    remaining = request.session.get('remaining', BATCH_SIZE)
    request.session['remaining'] = remaining - 1

    annotation.save()

    return JsonResponse({'status': 200})


def log_in(request):
    if request.method == 'GET':
        return redirect('/')

    username, password = request.POST['username'], request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('/')
    else:
        return redirect('/join?login_error=True')


def sign_up(request):
    if request.user.is_authenticated and not _is_temp(request.user):
        return redirect('/annotate')

    if request.method == 'GET':
        if 'error' in request.GET:
            return render(request, 'signup.html', {
                'profile': Profile.objects.get(user=request.user),
                'error': request.GET['error']
            })
        else:
            return render(request, 'signup.html', {
                'profile': Profile.objects.get(user=request.user)
            })

    username = request.POST['username']
    password = request.POST['password']
    password2 = request.POST['password2']
    user_source = request.POST['user_source']

    if User.objects.filter(username=username).exists():
        return redirect('/signup?error=0')

    if re.search('^(\\w|\\.|\\_|\\-)+[@](\\w|\\_|\\-|\\.)+[.]\\w{2,3}$', username):
        return redirect('/signup?error=1')

    if password != password2:
        return redirect('/signup?error=2')

    try:
        validate_password(password)
    except ValidationError as e:
        for error_string in e:
            if error_string == 'This password is too short. It must contain at least 8 characters.':
                return redirect('/signup?error=3')
            elif error_string == 'This password is too common.':
                return redirect('/signup?error=4')
            elif error_string == 'This password is entirely numeric.':
                return redirect('/signup?error=5')
            else:
                return redirect('/signup?error=6')

    # handle logic for saving progress
    if request.user.is_authenticated and _is_temp(request.user):
        request.user.set_password(password)
        request.user.username = username
        request.user.save()
        login(request, request.user)

        profile = Profile.objects.get(user=request.user)
        profile.is_temporary = False
        profile.save()

        assert request.user.is_authenticated and request.user.username == username
        return redirect('/profile/' + request.user.username)
    else:
        # handle first-time user creation
        user = User.objects.create_user(
            username=username, email=None, password=password)
        profile = Profile.objects.create(user=user, source=user_source)
        login(request, user)

    return redirect('/help')


def log_out(request):
    logout(request)
    return redirect('/')
