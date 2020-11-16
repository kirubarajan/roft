import uuid
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """A wrapper around the User class to store state for a given user"""
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    is_turker = models.BooleanField(default=False)
    source = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username + " " + str(self.is_turker)


class Tag(models.Model):
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    human = models.BooleanField()

    def __str__(self):
        return self.text


class Prompt(models.Model):
    """Human written sentence that gets continued."""
    body = models.TextField()

    def __str__(self):
        return self.body


class EvaluationText(models.Model):
    """The continuation associated with the prompt."""
    prompt = models.ForeignKey(Prompt, on_delete=models.DO_NOTHING)
    body = models.TextField()
    boundary = models.IntegerField()

    def __str__(self):
        return self.body


class Annotation(models.Model):
    """A human annotation of a prompt-continuation pair."""
    timestamp = models.DateTimeField(auto_now=True, null=True)
    annotator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    text = models.ForeignKey(EvaluationText, on_delete=models.DO_NOTHING)
    boundary = models.IntegerField()
    tags = models.ManyToManyField(Tag, related_name="annotation_tags")
    revision = models.TextField()
    points = models.IntegerField()
    attention_check = models.BooleanField(default=False)

    def __str__(self):
        return self.annotator.username + " " + str(self.timestamp)


class Group(models.Model):
    """A grouping of several prompt-continuation pairs."""
    name = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    evaluation_texts = models.ManyToManyField(EvaluationText)
    version = models.FloatField(null=True)
    decoding_strategy = models.CharField(max_length=100, null=True)
    decoding_strategy_value = models.FloatField(null=True)
    dataset_origin = models.URLField(null=True)

    def __str__(self):
        return self.name
