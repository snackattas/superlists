from django.test import TestCase
from django.http import HttpRequest
from django.utils.html import escape
from django.core.urlresolvers import resolve
from django.contrib.auth import get_user_model
import logging
from unittest.mock import patch, Mock
from lists.views import home_page
from lists.models import Item, List
from lists.forms import (
    DUPLICATE_ITEM_ERROR, EMPTY_ITEM_ERROR,
    NONEXISTENT_USER_EMAIL_ERROR, SAME_EMAIL_ERROR,
    ExistingListItemForm, ItemForm)
import unittest

from django.http import HttpRequest
from lists.views import new_list

User = get_user_model()


@patch('lists.views.NewListForm')
class NewListViewUnitTest(unittest.TestCase):

    def setUp(self):
        self.request = HttpRequest()
        self.request.POST['text'] = 'new list item'
        self.request.user = Mock()

    def test_passes_POST_data_to_NewListForm(self, mockNewListForm):
        new_list(self.request)
        mockNewListForm.assert_called_once_with(data=self.request.POST)

    def test_saves_form_with_owner_if_form_valid(self, mockNewListForm):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True
        new_list(self.request)
        mock_form.save.assert_called_once_with(owner=self.request.user)

    @patch('lists.views.redirect')
    def test_redirects_to_form_returned_object_if_form_valid(
        self, mock_redirect, mockNewListForm
    ):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True

        response = new_list(self.request)

        self.assertEqual(response, mock_redirect.return_value)
        mock_redirect.assert_called_once_with(mock_form.save.return_value)

    @patch('lists.views.render')
    def test_renders_home_template_with_form_if_form_invalid(
        self, mock_render, mockNewListForm
    ):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False

        response = new_list(self.request)

        self.assertEqual(response, mock_render.return_value)
        mock_render.assert_called_once_with(
            self.request, 'home.html', {'form': mock_form})

    def test_does_not_save_if_form_invalid(self, mockNewListForm):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False
        new_list(self.request)
        self.assertFalse(mock_form.save.called)


class HomePageTest(TestCase):

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')


    def test_home_page_uses_item_form(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], ItemForm)


class NewListViewsIntegratedTest(TestCase):

    def test_can_save_a_POST_request(self):
        self.client.post('/lists/new', data={'text': 'A new list item'})
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new list item')

    def test_for_invalid_input_doesnt_save_but_shows_errors(self):
        response = self.client.post('/lists/new', data={'text': ''})
        self.assertEqual(List.objects.count(), 0)
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))

    def test_list_owner_is_saved_if_user_is_authenticated(self):
        user = User.objects.create(email='a@b.com')
        self.client.force_login(user)
        self.client.post('/lists/new', data={'text': 'new item'})
        list_ = List.objects.first()
        self.assertEqual(list_.owner, user)

class ListViewTest(TestCase):

    def test_displays_item_form(self):
        list_ = List.objects.create()
        response = self.client.get('/lists/%d/' % (list_.id,))
        self.assertIsInstance(response.context['form'], ExistingListItemForm)
        self.assertContains(response, 'name="text"')


    def test_uses_list_template(self):
        list_ = List.objects.create()
        response = self.client.get('/lists/%d/' % (list_.id,))
        self.assertTemplateUsed(response, 'list.html')


    def test_displays_only_items_for_that_list(self):
        correct_list = List.objects.create()
        Item.objects.create(text='itemey 1', list=correct_list)
        Item.objects.create(text='itemey 2', list=correct_list)
        other_list = List.objects.create()
        Item.objects.create(text='other list item 1', list=other_list)
        Item.objects.create(text='other list item 2', list=other_list)

        response = self.client.get('/lists/%d/' % (correct_list.id,))

        self.assertContains(response, 'itemey 1')
        self.assertContains(response, 'itemey 2')
        self.assertNotContains(response, 'other list item 1')
        self.assertNotContains(response, 'other list item 2')


    def test_passes_correct_list_to_template(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()
        response = self.client.get('/lists/%d/' % (correct_list.id,))
        self.assertEqual(response.context['list'], correct_list)


    def test_can_save_a_POST_request_to_an_existing_list(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()

        self.client.post(
            '/lists/%d/' % (correct_list.id,),
            data={'text': 'A new item for an existing list'})

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new item for an existing list')
        self.assertEqual(new_item.list, correct_list)


    def test_POST_redirects_to_list_view(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()

        response = self.client.post(
            '/lists/%d/' % (correct_list.id,),
            data={'text': 'A new item for an existing list'})
        self.assertRedirects(response, '/lists/%d/' % (correct_list.id,))


    def post_invalid_input(self):
        list_ = List.objects.create()
        return self.client.post(
            '/lists/%d/' % (list_.id,),
            data={'text': ''}
        )


    def test_for_invalid_input_nothing_saved_to_db(self):
        self.post_invalid_input()
        self.assertEqual(Item.objects.count(), 0)


    def test_for_invalid_input_renders_list_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')


    def test_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context['form'], ExistingListItemForm)


    def test_for_invalid_input_shows_error_on_page(self):
        response = self.post_invalid_input()
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))


    def test_duplicate_item_validation_errors_end_up_on_lists_page(self):
        list1 = List.objects.create()
        item1 = Item.objects.create(list=list1, text='textey')
        response = self.client.post(
            '/lists/%d/' % (list1.id,),
            data={'text': 'textey'})

        expected_error = escape(DUPLICATE_ITEM_ERROR)
        self.assertContains(response, expected_error)
        self.assertTemplateUsed(response, 'list.html')
        self.assertEqual(Item.objects.all().count(), 1)

    def test_POST_for_share_list_redirects_to_lists_page(self):
        list_ = List.objects.create()
        response = self.client.post('/lists/%d/share/' % (list_.id,), data={'email':'junk@junk.com'})
        self.assertTemplateUsed(response, 'list.html')

class ListViewOwnerTest(TestCase):

    def test_shows_owner_when_list_has_owner(self):
        user = User.objects.create(email="user@gmail.com")
        list_ = List.create_new("test", owner=user)
        response = self.client.post('/lists/%d/' % (list_.id,))
        self.assertContains(response, "List owner:")
        self.assertContains(response, user.email)

    def test_does_not_show_owner_when_list_doesnt_have_owner(self):
        list_ = List.create_new("test")
        response = self.client.post('/lists/%d/' % (list_.id,))
        self.assertNotContains(response, "List owner:")

class ListViewShareListFormTest(TestCase):

    def test_shared_with_adds_user_to_list(self):
        share_with = User.objects.create(email="shared@gmail.com")
        list_ = List.objects.create()
        self.client.post('/lists/%d/share/' % (list_.id),
            data={'share_with':share_with.email})
        self.assertEqual(list_.shared_with.all().count(), 1)
        self.assertEqual(list_.shared_with.first(), share_with)

    def test_shared_with_adds_user_to_list_on_owned_list(self):
        user = User.objects.create(email="user@gmail.com")
        share_with = User.objects.create(email="shared@gmail.com")
        list_ = List.objects.create(owner=user)
        self.client.post('/lists/%d/share/' % (list_.id),
            data={'share_with':share_with.email})
        self.assertEqual(list_.shared_with.all().count(), 1)
        self.assertEqual(list_.shared_with.first(), share_with)

    def test_shared_with_adds_users_to_list(self):
        user1 = User.objects.create(email="user1@gmail.com")
        user2 = User.objects.create(email="user2@gmail.com")
        list_ = List.objects.create()
        self.client.post('/lists/%d/share/' % (list_.id),
            data={'share_with':user1.email})
        self.assertEqual(list_.shared_with.all().count(), 1)
        self.client.post('/lists/%d/share/' % (list_.id),
            data={'share_with':user2.email})
        self.assertEqual(list_.shared_with.all().count(), 2)
        self.assertQuerysetEqual(list_.shared_with.all().order_by("email"), map(repr, [user1,user2]))

    def test_for_adding_nonexistent_user(self):
        list_ = List.objects.create()
        response = self.client.post('/lists/%d/share/' % (list_.id,),\
            data={'share_with': "fakeuser@email.com"})
        self.assertContains(response,\
            escape(NONEXISTENT_USER_EMAIL_ERROR))

    def test_for_adding_badly_formatted_email(self):
        list_ = List.objects.create()
        response = self.client.post('/lists/%d/share/'  % (list_.id,),\
            data={'share_with': "bademail@email"})
        self.assertContains(response,\
            escape("Enter a valid email address."))

    def test_for_adding_blank(self):
        list_ = List.objects.create()
        response = self.client.post('/lists/%d/share/'  % (list_.id,),\
            data={'share_with': ""})
        self.assertContains(response,\
            escape("This field is required."))

class MyListsTest(TestCase):

    def test_my_lists_url_renders_my_lists_template(self):
        User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertTemplateUsed(response, 'my_lists.html')


    def test_passes_correct_owner_to_template(self):
        User.objects.create(email='wrong@owner.com')
        correct_user = User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertEqual(response.context['owner'], correct_user)

    def test_user_shares_list_and_it_shows_up_in_sharees_my_lists(self):
        user = User.objects.create(email='a@b.com')
        share_with = User.objects.create(email="c@d.com")
        list_ = List.create_new("item", owner=user)
        self.client.post("/lists/%d/share/" % (list_.id),\
            data={'share_with': share_with.email})
        response = self.client.get('/lists/users/%s/' % (share_with.email,))
        self.assertContains(response, share_with.email)
