import uuid
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """A wrapper around the User class to store state for a given user"""
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    is_turker = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username + " " + str(self.is_turker)


class System(models.Model):
    """The model that generated a given Generation."""
    name = models.CharField(max_length=200)
    description = models.TextField()
    dataset_origin = models.URLField(null=True)


class Prompt(models.Model):
    """Human written sentence that gets continued."""
    body = models.TextField()

    def __str__(self):
        return self.body


class Generation(models.Model):
    """The continuation associated with the prompt."""
    system = models.ForeignKey(System, on_delete=models.DO_NOTHING)
    prompt = models.ForeignKey(Prompt, on_delete=models.DO_NOTHING)
    body = models.TextField()
    boundary = models.IntegerField()
    decoding_strategy = models.CharField(max_length=100, null=True)
    decoding_strategy_value = models.FloatField(null=True)

    def __str__(self):
        return self.body


class Annotation(models.Model):
    """A human annotation of a prompt-continuation pair."""
    annotator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField(auto_now=True, null=True)
    generation = models.ForeignKey(Generation, on_delete=models.DO_NOTHING)
    boundary = models.IntegerField()
    points = models.IntegerField()
    revision = models.TextField()
    attention_check = models.BooleanField(default=False)

    def __str__(self):
        return self.annotator.username + " " + str(self.timestamp)


class Playlist(models.Model):
    """A grouping of several prompt-continuation pairs."""
    name = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    prompts = models.ManyToManyField(Prompt)
    version = models.FloatField(null=True)

    def __str__(self):
        return self.name


# deprecated
class Tag(models.Model):
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    human = models.BooleanField()

    def __str__(self):
        return self.text