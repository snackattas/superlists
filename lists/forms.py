from django import forms
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import logging
from lists.models import Item, List
from django.contrib.auth import get_user_model

User = get_user_model()
EMPTY_ITEM_ERROR = "You can't have an empty list item"
DUPLICATE_ITEM_ERROR = "You've already got this in your list"
NONEXISTENT_USER_EMAIL_ERROR = "The email provided is not a valid user's email"
SAME_EMAIL_ERROR = "You can't share a list with yourself"


class ItemForm(forms.models.ModelForm):
    class Meta:

        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.fields.TextInput(attrs={
                'placeholder': 'Enter a to-do item',
                'class': 'form-control input-lg',}),}

        error_messages = {
            'text': {'required': EMPTY_ITEM_ERROR}}

class ExistingListItemForm(ItemForm):
    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.list = for_list


    def validate_unique(self):
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            e.error_dict = {'text': [DUPLICATE_ITEM_ERROR]}
            self._update_errors(e)


class NewListForm(ItemForm):

    def save(self, owner):
        if owner.is_authenticated:
            return List.create_new(first_item_text=self.cleaned_data['text'], owner=owner)
        else:
            return List.create_new(first_item_text=self.cleaned_data['text'])

class ShareListForm(forms.Form):

    def __init__(self, for_list=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list = for_list

    share_with = forms.EmailField(widget=forms.TextInput(attrs={
        'placeholder': 'your-friend@example.com',
        'class': 'form-control input-sm'}))

    def clean_share_with(self):
        email = self.cleaned_data['share_with']
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist as e:
            raise ValidationError(NONEXISTENT_USER_EMAIL_ERROR)
        if self.list.owner:
            if email == self.list.owner.email:
                raise ValidationError(SAME_EMAIL_ERROR)
        return email

    def save(self):
        self.list.shared_with.add(self.cleaned_data['share_with'])
