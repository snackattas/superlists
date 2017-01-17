from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings

class List(models.Model):
<<<<<<< HEAD
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
=======

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

>>>>>>> 716a2840d4c0fde5bc78357deb5be12fe7a65f32
    def get_absolute_url(self):
        return reverse('view_list', args=[self.id])

    def __str__(self):
        return str(self.id)

    @staticmethod
    def create_new(first_item_text, owner=None):
        list_ = List.objects.create(owner=owner)
        Item.objects.create(text=first_item_text, list=list_)
        return list_

    @property
    def name(self):
        return self.item_set.first().text

class Item(models.Model):

    text = models.TextField(default='')
    list = models.ForeignKey(List, default=None)

    class Meta:
        ordering = ('id',)
        unique_together = ('list', 'text')

    def __str__(self):
        return self.text
