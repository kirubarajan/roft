import uuid
from django.db import models
from django.contrib.auth.models import User


SEP = "_SEP_"


class Profile(models.Model):
    """A wrapper around the User class to store state for a given user"""
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    is_turker = models.BooleanField(default=False)
    is_temporary = models.BooleanField(default=False)
    source = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username + " " + str(self.is_turker)


class System(models.Model):
    """The model that generated a given Generation."""
    name = models.CharField(max_length=200, primary_key=True)
    description = models.TextField()

    # @kirubarajan: is this for training data or fine-tuning?
    finetuned_dataset_location = models.URLField(null=True)


class Dataset(models.Model):
    """Dataset that we sample prompts/true human continuations from."""
    class Meta:
        unique_together = (("name", "split"),)

    name = models.CharField(max_length=128)
    split = models.CharField(max_length=16)


class Prompt(models.Model):
    """Human written sentence that gets continued."""
    class Meta:
        unique_together = (("dataset", "prompt_index"),)

    body = models.TextField()
    num_sentences = models.IntegerField()
    dataset = models.ForeignKey(Dataset, on_delete=models.DO_NOTHING)
    prompt_index = models.IntegerField()

    def __str__(self):
        return self.body


class DecodingStrategy(models.Model):
    """Meta-data about generation strategy used for a Generation object. """
    class Meta:
        unique_together = (("name", "value"),)

    name = models.CharField(max_length=128)
    value = models.FloatField(null=True)


class Generation(models.Model):
    """The continuation associated with the prompt."""
    system = models.ForeignKey(System, on_delete=models.DO_NOTHING)
    prompt = models.ForeignKey(Prompt, on_delete=models.DO_NOTHING)
    decoding_strategy = models.ForeignKey(
        DecodingStrategy, on_delete=models.DO_NOTHING)
    body = models.TextField()

    @property
    def boundary(self):
        # TODO(daphne): Should there be a +1 here?
        return self.prompt.num_sentences - 1

    def __str__(self):
        return self.body


class FeedbackOption(models.Model):
    """The types of reasons people give for thinking sentence is machine generated text"""
    shortname = models.CharField(max_length=40, primary_key=True)
    description = models.CharField(max_length=250)
    category = models.CharField(max_length=20)
    is_default = models.BooleanField(default=True)

    def __str__(self):
        return self.description


class Annotation(models.Model):
    """A human annotation of a prompt-continuation pair."""
    date = models.DateTimeField(auto_now=True, null=True)
    annotator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    generation = models.ForeignKey(Generation, on_delete=models.DO_NOTHING)
    playlist = models.CharField(max_length=30, default='')
    boundary = models.IntegerField()
    points = models.IntegerField()
    reason = models.ManyToManyField(FeedbackOption)
    attention_check = models.BooleanField(default=False)

    def __str__(self):
        return self.annotator.username + " " + str(self.date)


class Timestamp(models.Model):
    """When a continuation/decision was made. First Timestamp is annotation start,
    last is annotation submit, and in-between are for different continuations."""
    annotation = models.ForeignKey(Annotation, on_delete=models.DO_NOTHING)
    date = models.DateTimeField()


class Playlist(models.Model):
    """A grouping of several prompt-continuation pairs."""
    class Meta:
        unique_together = (("shortname", "version"),)

    shortname = models.CharField(max_length=32)
    name = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    details = models.TextField(blank=True)
    generations = models.ManyToManyField(Generation)
    version = models.CharField(max_length=8)

    def __str__(self):
        return self.name


# deprecated
class Tag(models.Model):
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    human = models.BooleanField()

    def __str__(self):
        return self.text
