import ast
import json
import random
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from core.models import Prompt, Tag, EvaluationText, Annotation


def onboard(request):
    return render(request, "onboard.html", {})


def annotate(request):
    text = random.choice(EvaluationText.objects.all())
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

    grammar = request.POST['grammar'] == 'true'
    repetition = request.POST['repetition'] == 'true'
    entailment = request.POST['entailment'] == 'true'
    sense = request.POST['sense'] == 'true'

    annotation = Annotation.objects.create(
        annotator=request.user,
        text=EvaluationText.objects.get(pk=text),
        boundary=boundary,
        revision=revision
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
        return redirect('/annotate')


def sign_up(request):
    email, username, password = request.POST['email'], request.POST['username'], request.POST['password']
    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    return redirect('/annotate')


def log_out(request):
    logout(request)
    return redirect('/')