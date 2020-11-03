from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
# from django.db.models import Q

from decimal import *

from .models import User, Listing, Bid, Comment
from .decorators import Unauthenticated_user, Authenticated_user

# dictionary to store all the data from the models
model_data = {
    'Listings': Listing.objects.all(),
    'Bids': Bid.objects.all(),
    'Comments': Comment.objects.all(),
}

# dictionary variable to keep track of individual's watchlist
watch_list = dict()

def index(request):
    listings = model_data['Listings']
    context = {
        'listings': listings,
    }
    return render(request, "auctions/index.html", context)

@Unauthenticated_user
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


@Authenticated_user
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


@Unauthenticated_user
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")

@Authenticated_user
def listing(request, listing):
    item = Listing.objects.get(pk=listing)
    old_bid = Bid.objects.filter(listing=item)
    comments = Comment.objects.filter(listing=item)
    if old_bid.count() is 1:
        default_bid = old_bid[0].highest_bid + 10
    else:
        default_bid = item.initial + 10
    try:
        bid_info = Bid.objects.get(listing=item)
    except:
        bid_info = None;
    context = {
        'listing': item,
        'bid': bid_info,
        'comments': comments,
        'default_bid': default_bid,
    }
    return render(request, "auctions/listing.html", context)

@Authenticated_user
def bid(request):
    if request.method == "POST":
        new_bid = request.POST["bid"]
        item_id = request.POST["list_id"]

        item = Listing.objects.get(pk=item_id)
        old_bid = Bid.objects.filter(listing=item)

        if old_bid.count() is not 1:
            bid = Bid(user=request.user, listing=item, highest_bid=new_bid)
            bid.save()
        elif Decimal(new_bid) < old_bid[0].highest_bid:
            comments = Comment.objects.filter(listing=item)
            default_bid = old_bid[0].highest_bid + 10
            message = "The bid you placed was lower than needed"
            context = {
                'listing': item,
                'bid': old_bid[0],
                'comments': comments,
                'default_bid': default_bid,
                'message': message,
            }
            return render(request, "auctions/listing.html", context)
        else:
            old_bid.update(highest_bid=new_bid, user=request.user)
    return redirect("auctions:listing", item_id)

@Authenticated_user
def comment(request):
    if request.method == "POST":
        content = request.POST["content"]
        item_id = request.POST["list_id"]
        item = Listing.objects.get(pk=item_id)
        newComment = Comment(user=request.user, comment=content, listing=item)
        newComment.save()
        return redirect("auctions:listing", item_id)
    return redirect("auctions:index")

@Authenticated_user
def watchlist(request):
    if request.user not in watch_list:
        context = {
            'message': "Nothing in your watchlist",
        }
        return render(request, "auctions/watchlist.html", context)
    listings = []
    for item in watch_list[request.user]:
        list_item = Listing.objects.get(pk=item)
        listings.append(list_item)
    context = {
        'listings': listings,
    }
    return render(request, "auctions/watchlist.html", context)

@Authenticated_user
def add_to_watchlist(request, item_id):
    if request.user not in watch_list:
        watch_list[request.user] = []
        watch_list[request.user].append(item_id)
        message = "Successfully added item to your WatchList"
    elif item_id in watch_list[request.user]:
        message = "Item already present in your WatchList"
    else:
        watch_list[request.user].append(item_id)
        message = "Successfully added item to your WatchList"
    listings = model_data['Listings']
    context = {
        'listings': listings,
        'message': message,
    }
    return render(request, "auctions/index.html", context)

@Authenticated_user
def remove_from(request, item_id):
    if request.user not in watch_list:
        message = "Cannot remove from empty WatchList"
    elif item_id in watch_list[request.user]:
        watch_list[request.user].remove(item_id)
        message = "Successfully removed item from your WatchList"
    else:
        message = "Item not in your WatchList"
    listings = model_data['Listings']
    context = {
        'listings': listings,
        'message': message,
    }
    return render(request, "auctions/index.html", context)

def categories(request):
    category = dict()
    listings = model_data['Listings']
    for item in listings:
        if item.category not in category:
            category[item.category] = []
            category[item.category].append(item)
        else:
            category[item.category].append(item)
    context = {
        'category_list': category,
    }
    return render(request, "auctions/category.html", context)
