from flask import Blueprint, request, render_template, redirect, url_for, flash
import string
from datetime import date, datetime
from eventwave_app.models import User, Event, Comment
import requests
from datetime import datetime
from sorcery import dict_of
# Import app and db from events_app package so that we can run app
from eventwave_app.extensions import app, db
from eventwave_app.forms import SignUpForm
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from eventwave_app.forms import LoginForm
from flask_login import login_user, login_required, logout_user, current_user

BASE_URL = 'https://api.seatgeek.com/2/events?'
PER_PAGE = '&per_page=20'
CLIENT_ID = "&client_id=MjAxNTMyNjV8MTY1MTE4OTU5My40NDUzMzAx"

main = Blueprint("main", __name__)
auth = Blueprint("auth", __name__)
bcrypt = Bcrypt()

##########################################
#           Routes                       #
##########################################


@main.route('/')
def homepage():
    """Functions makes an API call to get event data for Landing Page"""
    response = requests.get(
        "https://api.seatgeek.com/2/events?id=6294887&client_id=MjAxNTMyNjV8MTY1MTE4OTU5My40NDUzMzAx")
    # converts response to JSON objects
    responseData = response.json()
    # variables from API
    title = responseData['events'][0]['title']
    seatgeek_id = responseData['events'][0]['id']
    url = responseData['events'][0]['url']
    pub = responseData['events'][0]['datetime_utc']
    performer = responseData['events'][0]['performers'][0]['name']
    performers = responseData['events'][0]['performers']
    performerArray = []
    # creates an array of performers for each event
    for performer in performers:
        performerArray.append(performer['name'])

    kind = responseData['events'][0]['type']
    image = responseData['events'][0]['performers'][0]['image']

    context = {
        'title': title,
        'seatgeek_id': seatgeek_id,
        'url': url,
        'pub': pub,
        'performer': performer,
        'performers': performers,
        'performerArray': performerArray,
        'kind': kind,
        'image': image
    }
    
    return render_template('events/index.html', **context)

@main.route('/results', methods=['POST'])
def results():
    """Function makes an API call based on search parameters of user"""
#     # build query based on search parameters index page
    zip_code = request.form.get('zip')
    radius = request.form.get('radius')
    start = request.form.get('start')
    end = request.form.get('end')
    
    # if start and end was not entered
    if start == '' or end == '':
        query = f'{BASE_URL}geoip={str(zip_code)}&range={radius}mi{PER_PAGE}{CLIENT_ID}'
    else:
        query = f'{BASE_URL}geoip={zip_code}&range={radius}mi{PER_PAGE}&datetime_utc.gte={start}&datetime_utc.lte={end}{CLIENT_ID}'

#     # api call
    response = requests.get(query)
    responseData = response.json()

#     # compile variables
    if response:
        eventsContext = []
        for event in responseData['events']:
            title = event['title']
            seatgeek_id = event['id']
            url = event['url']
            pub = event['datetime_utc']
            kind = event['type']
            image = event['performers'][0]['image']
            # performer = event['performers'][1]['name']
            performers = event['performers']
            performerArray = []
            for performer in performers:
                performerArray.append(performer['name'])

            context = dict_of(title, seatgeek_id, url, pub, performer,
                              performers, performerArray, kind, image)
            eventsContext.append(context)

        return render_template('events/results.html', eventsContext=eventsContext)
    return redirect('/')

@main.route('/events/detail/<seatgeek_id>', methods=['GET', 'POST'])
@login_required
def events_details(seatgeek_id):
    """Function makes an API call to gather data for the detail's page"""
    
    query = f'{BASE_URL}id={seatgeek_id}{CLIENT_ID}'
    # API Call
    response = requests.get(query)
    responseData = response.json()

    # Build Context for event selected
    title = responseData['events'][0]['title']
    seatgeek_id = responseData['events'][0]['id']
    url = responseData['events'][0]['url']
    pub = responseData['events'][0]['datetime_utc']
    performers = responseData['events'][0]['performers']
    performerArray = []
    for performer in performers:
        performerArray.append(performer['name'])
    kind = responseData['events'][0]['type']
    image = responseData['events'][0]['performers'][0]['image']

    context = dict_of(title, seatgeek_id, url, pub, performer,
                      performers, performerArray, kind, image)

    name_v2 = responseData['events'][0]['venue']['name_v2'].replace(" ", "+")
    address = responseData['events'][0]['venue']['address'].replace(" ", "+")
    extended_address = responseData['events'][0]['venue']['extended_address'].replace(
        " ", "+")

    googleEventTitle = title.replace(" ", "+")
    googleEventStart = pub.translate(str.maketrans('', '', string.punctuation))
    googleEventEnd = str(int(googleEventStart.replace("T", "")) + 1)
    googleEventEnd = googleEventEnd[:8] + 'T' + googleEventEnd[8:]
    googleEventDetails = f'&details=For+details,+link+here:+{url}'
    googleEventAddress = f'&location={name_v2}{address}{extended_address}'

    context['googleEventCalendarURL'] = f'https://calendar.google.com/calendar/r/eventedit?text={googleEventTitle}&dates={googleEventStart}/{googleEventEnd}{googleEventDetails}{googleEventAddress}'
    
    return render_template('events/detail.html', context=context)

@main.route('/dashboard/<seatgeek_id>', methods=['GET', 'POST'])
@login_required
# add event to users dashboard
def dashboard_add(seatgeek_id):
    """Function makes API call to gather data about event.
    Data is then stored in database and associated with User"""

    query = f'{BASE_URL}id={seatgeek_id}{CLIENT_ID}'
    # API Call
    response = requests.get(query)
    responseData = response.json()

    # Build Context and saved to database
    title = responseData['events'][0]['title']
    seatgeek_id = responseData['events'][0]['id']
    url = responseData['events'][0]['url']
    pub = responseData['events'][0]['datetime_utc']
    kind = responseData['events'][0]['type']
    image = responseData['events'][0]['performers'][0]['image']
    performers = responseData['events'][0]['performers']
    venue = responseData['events'][0]['venue']['name']
    performerArray = []
    for performer in performers:
        performerArray.append(performer['name'])
    if len(performerArray) > 2:
        performerString = ' '.join(performerArray[:2])
    else:
        performerString = ' '.join(performerArray)

    event = Event(title=title,
                  seatgeek_id=seatgeek_id,
                  url=url,
                  date_time=pub,
                  venue=venue,
                  performer=performerString,
                  image=image,
                  created_by_id=current_user.id)
    
    db.session.add(event)
    db.session.commit()
    flash('Event was added to your dashboard.')
    return redirect('/dashboard')

@main.route('/dashboard/delete/<seatgeek_id>', methods=['GET', 'POST'])
@login_required
def dashboard_delete(seatgeek_id):
    """Function deletes event from user's dashboard"""
    event = Event.query.filter_by(created_by_id=current_user.id, seatgeek_id=seatgeek_id).first()
    
    if event:
        db.session.delete(event)
        db.session.commit()
        flash('Event was removed from your dashboard.')
    else:
        flash('Event not found.')
    return redirect('/dashboard')


@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard_index():
    """Function gets all events associated with a User"""
    
    # Query to find all events saved by a specific user
    user_events = Event.query.filter_by(created_by_id=current_user.id).all()
    

    return render_template('dashboard/index.html', context=user_events)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash('Account Created')
        return redirect(url_for('auth.login'))

    return render_template('signup.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        login_user(user, remember=True)
        next_page = request.args.get('next')
        return redirect(next_page if next_page else url_for('main.homepage'))

    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.homepage'))


@main.route('/about', methods=['GET'])
def about():
    return render_template('about/about.html')