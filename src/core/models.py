from django.db import models

class Prompt(models.Model):
    body = models.TextField()

    def __str__(self):
        return self.body

class Tag(models.Model):
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=100)

    def __str__(self):
        return self.text

class EvaluationText(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.DO_NOTHING)
    body = models.TextField()
    boundary = models.IntegerField()

    def __str__(self):
        return self.body

class Annotation(models.Model):
    timestamp = models.DateTimeField(auto_now=True, null=True)
    annotator = models.CharField(max_length=100)
    text = models.ForeignKey(EvaluationText, on_delete=models.DO_NOTHING)
    boundary = models.IntegerField() # user's prediction
    tags = models.ManyToManyField(Tag, related_name="annotation_tags")
    note = models.TextField()

    def __str__(self):
        return self.annotator + " " + str(self.timestamp)