from flask import render_template,url_for, flash, redirect, session, request
from movie.forms import RegistrationForm, LoginForm
from movie import app, db, bcrypt, mongo, colab, matrix
from movie.models import User
from bson import ObjectId
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route('/home')
def home():
    topRated = mongo.db.movies.aggregate([ { '$sample': { 'size': 12 } } ])
    newReleases = mongo.db.movies.aggregate([ { '$sample': { 'size': 12 } } ])
    comingSoon = mongo.db.movies.aggregate([ { '$sample': { 'size': 12 } } ])
    return render_template('home.html', title='Home', topRated=topRated, newReleases=newReleases, comingSoon=comingSoon)

@app.route("/about")
def about():
    return render_template('rate.html')

@app.route('/register', methods=['GET',  'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password).save()
        flash(f'Account created for {form.username.data}!You will be able to login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title="Register", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful', 'danger')
    return render_template('login.html', title="Login", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/rate', methods=['GET', 'POST'])
@login_required
def rate():
    movies = mongo.db.movies.aggregate([ { '$sample': { 'size': 50 } } ])
    if request.method == 'POST':
        movie = request.form.get('movie_id')
        rating = request.form.get('rating')
        mongo.db.users.update({ "_id": ObjectId(current_user.get_id())},
        { "$set": { 'ratings.'+str(movie) : int(rating)}})
        flash(f'Movie {movie} Rated {rating}', 'success')
    return render_template('rate.html', title='Rate-Movies', movies=movies)

@app.route('/pred', methods=['GET', 'POST'])
@login_required
def pred():
    movies = mongo.db.users.find_one({"_id": ObjectId(current_user.get_id())})
    
    pred_movies_ind_user, pred_movies_ind_item = colab.predictions(movies['ratings'])
    pred_movies_ind_user = pred_movies_ind_user.tolist()
    pred_movies_ind_item = pred_movies_ind_item.tolist()
    pred_movies_user = mongo.db.movies.find({ "mov_index": { "$in": pred_movies_ind_user } })
    pred_movies_item = mongo.db.movies.find({ "mov_index": { "$in": pred_movies_ind_item } })
    
    pred_movies_mat = matrix.predictions(movies['ratings'])

    return render_template('pred.html', title='Predicted-Movies', movies_user=pred_movies_user, movies_item=pred_movies_item, movies_mat=pred_movies_mat)
