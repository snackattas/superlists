from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from lists.forms import ExistingListItemForm, ItemForm, NewListForm, ShareListForm
from lists.models import Item, List
import logging
User = get_user_model()

# Create your views here.
def home_page(request):
    return render(request, 'home.html', {'form': ItemForm()})

def new_list(request):
    form = NewListForm(data=request.POST)
    if form.is_valid():
        list_ = form.save(owner=request.user)
        return redirect(list_)
    return render(request, 'home.html', {'form': form})

def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    form = ExistingListItemForm(for_list=list_)
    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(list_)
    return render(request, 'list.html', {'list': list_, "form": form, 'share_form': ShareListForm()})

def my_lists(request, email):
    owner = User.objects.get(email=email)
    return render(request, 'my_lists.html', {'owner': owner})

def share_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    if request.method == "POST":
        share_form = ShareListForm(list_, data=request.POST)
        if share_form.is_valid():
            share_form.save()
            return redirect(list_)
        return render(request, 'list.html', {'list': list_, "form": ExistingListItemForm(for_list=list_), 'share_form':share_form})
    return redirect(list_)
