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
_PLAYLIST_VERSION = "0.5"


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
    return render(request, "help.html", {})


def about(request):
    return render(request, "about.html", {})


def join(request):
    return redirect('/about')


def play(request):
    return redirect('/about')

def _leaderboard_is_stale():
    current_time = datetime.now()
    if leaderboard_cache_time:
        elapsed_time = current_time - leaderboard_cache_time
        elapsed_minutes = divmod(elapsed_time.total_seconds(), 60)
        return elapsed_minutes > 15
    else:
        return True


def leaderboard(request):
    return redirect('/about')


def profile(request, username):
    return redirect('/about')


def annotate(request):
    return redirect('/about')


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
    return redirect('/about')


def sign_up(request):
    return redirect('/about')


def log_out(request):
    return redirect('/about')
