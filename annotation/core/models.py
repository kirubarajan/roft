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

    # @kirubarajan: is this for training data or fine-tuning?
    dataset_origin = models.URLField(null=True)


class Dataset(models.Model):
    """Dataset that we sample prompts/true human continuations from."""
    name = models.CharField(max_length=128)
    split = models.CharField(max_length=16)


class Prompt(models.Model):
    """Human written sentence that gets continued."""
    body = models.TextField()

    def __str__(self):
        return self.body


class DecodingStrategy(models.Model):
    """Meta-data about generation strategy used for a Generation object. """
    name = models.CharField(max_length=128)
    value = models.FloatField(null=True)


class Generation(models.Model):
    """The continuation associated with the prompt."""
    system = models.ForeignKey(System, on_delete=models.DO_NOTHING)
    prompt = models.ForeignKey(Prompt, on_delete=models.DO_NOTHING)
    decoding_strategies = models.ManyToManyField(DecodingStrategy)
    body = models.TextField()
    boundary = models.IntegerField()

    def __str__(self):
        return self.body


class Annotation(models.Model):
    """A human annotation of a prompt-continuation pair."""
    timestamp = models.DateTimeField(auto_now=True, null=True)
    annotator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
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