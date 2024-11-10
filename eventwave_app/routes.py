from sqlalchemy.orm import joinedload
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

@main.route('/', methods=['GET'])
def homepage():
    """Landing Page"""
    return render_template('events/index.html')

@main.route('/results', methods=['POST'])
def results():
    zip_code = request.form.get('zip')
    radius = request.form.get('radius')
    query = f'{BASE_URL}geoip={str(zip_code)}&range={radius}mi{PER_PAGE}{CLIENT_ID}'
    response = requests.get(query)
    responseData = response.json()
    
    if response:
        eventsContext = []
        for event in responseData['events']:
            context = parse_event_data(event)
            eventsContext.append(context)
        return render_template('events/results.html', eventsContext=eventsContext)
    return redirect('/')

@main.route('/events/detail/<seatgeek_id>', methods=['GET', 'POST'])
@login_required
def events_details(seatgeek_id):
    """Function makes an API call to gather data for the detail's page"""
    query = f'{BASE_URL}id={seatgeek_id}{CLIENT_ID}'
    response = requests.get(query)
    responseData = response.json()

    context = parse_event_data(responseData['events'][0])

    name_v2 = responseData['events'][0]['venue']['name_v2'].replace(" ", "+")
    address = responseData['events'][0]['venue']['address'].replace(" ", "+")
    extended_address = responseData['events'][0]['venue']['extended_address'].replace(
        " ", "+")

    googleEventTitle = context['title'].replace(" ", "+")
    googleEventStart = context['pub'].translate(str.maketrans('', '', string.punctuation))
    googleEventEnd = str(int(googleEventStart.replace("T", "")) + 1)
    googleEventEnd = googleEventEnd[:8] + 'T' + googleEventEnd[8:]
    googleEventDetails = f'&details=For+details,+link+here:+{context["url"]}'
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
    response = requests.get(query)
    responseData = response.json()

    context = parse_event_data(responseData['events'][0])

    event = Event(
        title=context['title'],
        seatgeek_id=context['seatgeek_id'],
        url=context['url'],
        date_time=context['pub'],
        venue=context['venue'],
        performer=' '.join(context['performerArray'][:2]),
        image=context['image'],
        address=context['address'],
        created_by_id=current_user.id
    )
    
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
    
    # Query to find all events and their comments saved by a specific user
    user_events = Event.query\
    .options(joinedload(Event.comments))\
    .filter_by(created_by=current_user)\
    .all()
    
    return render_template('dashboard/index.html', context=user_events)

@main.route('/dashboard/comment/add/<seatgeek_id>', methods=['GET', 'POST'])
@login_required
def dashboard_add_comment(seatgeek_id):
    """Function adds a comment to an event in user's dashboard"""
    event = Event.query.filter_by(seatgeek_id=seatgeek_id, created_by_id=current_user.id).first()

    if not event:
        print("EVENT NOT FOUND")
        flash('Event not found.')
        return redirect('/dashboard')

    if request.method == 'POST':
        comment_text = request.form.get('comment')
        print(comment_text)
        if comment_text:
            comment = Comment(comment=comment_text, event=event, created_by_id=current_user.id)
            db.session.add(comment)
            db.session.commit()
            print('Comment added Successflly')
            flash('Comment added successfully.')
        else:
            flash('Comment cannot be empty.')
        return redirect('/dashboard')

    return render_template('dashboard/index.html', event=event)

@main.route('/dashboard/comment/delete/<comment_id>', methods=['GET', 'POST'])
@login_required
def dashboard_delete_comment(comment_id):
    """Function deletes event from user's dashboard"""
    comment = Comment.query.filter_by(id=comment_id, created_by_id=current_user.id).first()
    
    if comment:
        db.session.delete(comment)
        db.session.commit()
        print("Comment was deleted succesfully")
        flash('Comment was removed from your dashboard.')
    else:
        flash('Comment not found.')
    return redirect('/dashboard')

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


# Helper function to parse event data
def parse_event_data(event):
    title = event['title']
    seatgeek_id = event['id']
    url = event['url']
    date_start = format_date(event['datetime_utc'])
    pub = event['datetime_utc']
    kind = event['type']
    image = event['performers'][0]['image']
    performers = event['performers']
    performerArray = [performer['name'] for performer in performers]
    address = event['venue']['address']
    venue = event['venue']['name']
    return {
        'title': title,
        'seatgeek_id': seatgeek_id,
        'url': url,
        'pub': pub,
        'performers': performers,
        'performerArray': performerArray,
        'kind': kind,
        'image': image,
        'date_start': date_start,
        'address': address,
        'venue': venue 
    }


    
def format_date(date_string):
    date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')
    return date.strftime('%A, %B %d, %Y %I:%M %p')

