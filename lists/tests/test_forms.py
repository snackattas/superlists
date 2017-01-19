from django.test import TestCase
from lists.forms import (
    DUPLICATE_ITEM_ERROR, EMPTY_ITEM_ERROR,
    ExistingListItemForm, ItemForm, NewListForm, ShareListForm,
    NONEXISTENT_USER_EMAIL_ERROR, SAME_EMAIL_ERROR)
from lists.models import Item, List
import unittest
from unittest.mock import patch, Mock
import logging
from django.contrib.auth import get_user_model

User = get_user_model()

class NewListFormTest(unittest.TestCase):

    @patch('lists.forms.List.create_new')
    def test_save_creates_new_list_from_post_data_if_user_not_authenticated(
        self, mock_List_create_new
    ):
        user = Mock(is_authenticated=False)
        form = NewListForm(data={'text': 'new item text'})
        form.is_valid()
        form.save(owner=user)
        mock_List_create_new.assert_called_once_with(
            first_item_text='new item text')

    @patch('lists.forms.List.create_new')
    def test_save_creates_new_list_with_owner_if_user_authenticated(
        self, mock_List_create_new
    ):
        user = Mock(is_authenticated=True)
        form = NewListForm(data={'text': 'new item text'})
        form.is_valid()
        form.save(owner=user)
        mock_List_create_new.assert_called_once_with(
            first_item_text='new item text', owner=user)

    @patch('lists.forms.List.create_new')
    def test_save_returns_new_list_object(self, mock_List_create_new):
        user = Mock(is_authenticated=True)
        form = NewListForm(data={'text': 'new item text'})
        form.is_valid()
        response = form.save(owner=user)
        self.assertEqual(response, mock_List_create_new.return_value)

class ItemFormTest(TestCase):

    def test_form_renders_item_text_input(self):
        form = ItemForm()
        self.assertIn('placeholder="Enter a to-do item"', form.as_p())
        self.assertIn('class="form-control input-lg"', form.as_p())


    def test_form_validation_for_blank_items(self):
        form = ItemForm(data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['text'],[EMPTY_ITEM_ERROR])


class ExistingListItemFormTest(TestCase):

    def test_form_renders_item_text_input(self):
        list_ = List.objects.create()
        form = ExistingListItemForm(for_list=list_)
        self.assertIn('placeholder="Enter a to-do item"', form.as_p())


    def test_form_validation_for_blank_items(self):
        list_ = List.objects.create()
        form = ExistingListItemForm(for_list=list_, data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['text'], [EMPTY_ITEM_ERROR])


    def test_form_validation_for_duplicate_items(self):
        list_ = List.objects.create()
        Item.objects.create(list=list_, text='no twins!')
        form = ExistingListItemForm(for_list=list_, data={'text': 'no twins!'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['text'], [DUPLICATE_ITEM_ERROR])

    def test_form_save(self):
        list_ = List.objects.create()
        form = ExistingListItemForm(for_list=list_, data={'text': 'hi'})
        new_item = form.save()
        self.assertEqual(new_item, Item.objects.all()[0])


class ShareListFormTest(TestCase):
    def test_form_renders_input(self):
        list_ = List.objects.create()
        form = ShareListForm(list_)
        self.assertIn('placeholder="your-friend@example.com"', form.as_p())

    def test_form_validation_for_blank_items(self):
        list_ = List.objects.create()
        form = ShareListForm(list_)
        self.assertFalse(form.is_valid())

    def test_junk_post(self):
        list_= List.objects.create()
        form = ShareListForm(list_, data={'junk':'its junk'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['share_with'][0],\
            "This field is required.")

    def test_bad_email(self):
        list_= List.objects.create()
        form = ShareListForm(list_, data={'share_with':'bademail'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['share_with'][0],\
            "Enter a valid email address.")

    def test_nonexistent_email(self):
        list_= List.objects.create()
        form = ShareListForm(list_, data={'share_with':'a@gmail.com'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['share_with'][0],\
            NONEXISTENT_USER_EMAIL_ERROR)

    def test_same_users_email(self):
        user = User.objects.create(email="a@b.com")
        list_= List.objects.create(owner=user)
        form = ShareListForm(list_, data={'share_with': user.email})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['share_with'][0],\
            SAME_EMAIL_ERROR)

    def test_save_list_without_owner(self):
        user = User.objects.create(email="a@b.com")
        list_ = List.objects.create()
        form = ShareListForm(list_, data={'share_with': user.email})
        form.is_valid()
        form.save()

    def test_save_list_with_owner(self):
        user = User.objects.create(email="a@b.com")
        user2 = User.objects.create(email="c@d.com")
        list_ = List.objects.create(owner=user)
        form = ShareListForm(list_, data={'share_with': user2.email})
        form.is_valid()
        form.save()

    def test_share_list_cannot_be_valid_without_list_passed_in(self):
        user = User.objects.create(email="a@b.com")
        list_ = List.objects.create()
        form = ShareListForm(data={'share_with': user.email})
        with self.assertRaises(AttributeError):
            form.is_valid()
