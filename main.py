from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import plotly.express as px
import plotly.io as pi
from sqlalchemy import or_

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///music_app.db"

db = SQLAlchemy(app)
app.app_context().push()
app.config['SECRET_KEY'] = 'thisismymusicapp'

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False) 
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    playlist = db.relationship('playlist', back_populates='user')
    __tablename__ = 'User'

class Admin(db.Model):
    admin_id = db.Column(db.Integer, primary_key=True)
    adminname = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    __tablename__='Admin'

class Track:
    def __init__(self, name, image_url, mp3_url):
        self.name = name
        self.image_url = image_url
        self.mp3_url = mp3_url

class playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    songs = db.relationship('song', back_populates='playlist')
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    user = db.relationship('User', back_populates='playlist')

class song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    track = db.Column(db.String(255), nullable=False)
    creator = db.Column(db.String(255), nullable=False)
    lyrics = db.Column(db.Text, nullable=True)
    song_url=db.Column(db.Text)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id', ondelete='CASCADE'), nullable=True)
    playlist = db.relationship('playlist', back_populates='songs')
    ratings = db.Column(db.Float, default =0.0)

recommended_tracks = [
    {'id': 1, 'name': 'Rage of Sparta', 'creator': 'Gerard Marino'},
    {'id': 2, 'name': 'The Vengeful Spartan', 'creator': 'Gerard Marino'},
    {'id': 3, 'name': 'Smooth Criminal', 'creator': 'Michael Jackson'},
    {'id': 4, 'name': 'Shape of You', 'creator': 'Ed Sherran'},
    {'id': 5, 'name': 'Rap-God', 'creator': 'Eminem'},
    {'id': 6, 'name': 'Sweaters', 'creator': 'Ivan B'},
    {'id': 7, 'name': 'Aarambh hai Prachand-Remix', 'creator': 'Shrylox'},
    {'id': 8, 'name': 'Subtle Break', 'creator': 'Ghostrifter Official'},
    {'id': 9, 'name': 'Glow', 'creator': 'Scott Buckley'},
    {'id': 10, 'name': 'Cherry Metal', 'creator': 'Arthur Vyncke'},
    {'id': 11, 'name': 'Midnight Stroll', 'creator': 'Ghostrifter Official'}
]


def get_track_from_database(track_id):
    for track in recommended_tracks:
        if track['id'] == track_id:
            return track

@app.route('/')
def base_page():
    template_path = os.path.join(app.template_folder, 'base.html')
    print(f'templatepath is: {template_path}')
    return render_template('base.html')

@app.route('/userlogin', methods = ['POST','GET'])
def userlogin():
    if request.method == 'POST':
        uname = request.form['username']
        pword = request.form['password']
        user_entry = User.query.filter_by(username=uname).first()

        if user_entry is None:
            return render_template('userlogin.html', message="User not registered. Please register first.")
        if user_entry.password == pword:
            session['username'] = uname
            session['user_id'] = user_entry.user_id
            return redirect('/homepage')
        return render_template('userlogin.html', message="Incorrect password. Please try again.")
    return render_template('userlogin.html')

@app.route('/adminlogin', methods=['POST','GET'])
def adminlogin():
    if request.method == 'POST':
        adminname = request.form['adminname']
        pword = request.form['password']

        Admin_entry = Admin.query.filter_by(adminname=adminname).first()

        if Admin_entry is None:
            return render_template('adminlogin.html', message="Admin not registered")
        if Admin_entry.password == pword:
            session['adminname'] = adminname
            session['admin_id'] = Admin_entry.admin_id
            return redirect('/admindashboard')
        return render_template('adminlogin.html', message="Incorrect password. Please try again.")
    return render_template('adminlogin.html')


@app.route('/adminreg', methods = ['POST','GET'])
def adminreg():
    if request.method == 'POST':
        adminname = request.form['adminname']
        email = request.form['email']
        pword = request.form['password']

        existing_admin = Admin.query.filter_by(adminname=adminname).first()

        if existing_admin is not None:
            return render_template('adminreg.html', message='Admin already registered! Use different name.')

        new_admin = Admin(adminname=adminname, email=email, password=pword)
        db.session.add(new_admin)
        db.session.commit()

        session['adminname'] = adminname
        session['admin_id'] = new_admin.admin_id
        return redirect('/admindashboard')

    return render_template('adminreg.html')



@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        email = request.form['email']
        pword = request.form['password']

        existing_user = User.query.filter_by(username=uname).first()

        if existing_user is not None:
            return render_template('register.html', message='User already registered! Use different Username')

        new_user = User(username=uname, email=email, password=pword)
        db.session.add(new_user)
        db.session.commit()

        session['username'] = uname
        session['user_id'] = new_user.user_id
        return redirect('/homepage')

    return render_template('register.html')

@app.route('/homepage', methods=['POST', 'GET'])
def homepage():
    recommended_tracks = '1'
    playlists = playlist.query.all()
    newsongs = song.query.filter(song.id > 15).all()
    search= song.query.all()

    if request.method == 'POST':
        selected_track_index = request.form.get('selected_track')
        selected_track_index_for_new_song = request.form.get('selected_track_for_new_song')
        searchh = request.form.get('search_query')
        
        if searchh is not None:
            rating= song.query.filter_by(ratings=searchh).first()
            if rating:
                return redirect(url_for('songview', track_id=rating.id))
        if searchh is not None:
            song_match = song.query.filter_by(track=searchh).first()
            if song_match:
                return redirect(url_for('songview', track_id=song_match.id))
        if searchh is not None:
            creator_match=song.query.filter_by(creator=searchh).first()
            if creator_match:
                return redirect(url_for('songview', track_id=creator_match.id))
        if selected_track_index_for_new_song is not None:
            selected_track_index_for_new_song = int(selected_track_index_for_new_song)
            selected_track_index_for_new_song = song.query.get(selected_track_index_for_new_song)

            if selected_track_index_for_new_song:
                return redirect(url_for('songview', track_id=selected_track_index_for_new_song.id))

        if selected_track_index:
            song_avial=song.query.get(selected_track_index)
            if song_avial: 
                return redirect(url_for('songview', track_id=selected_track_index))
            else:
                return render_template('homepage.html', message= 'Song is in the process of complete deletion, it cannot be reviewed right now! Enjoy Listening to other Songs!', recommended_tracks=recommended_tracks, playlists=playlists, newsongs=newsongs)
        
        if 'delete' in request.form:
            delete_playlist= request.form.get('delete_playlist')
            if delete_playlist:
                delete_playlist_id = playlist.query.get(delete_playlist)
                if delete_playlist_id:
                    db.session.delete(delete_playlist_id)
                    db.session.commit()
        return redirect(url_for('homepage'))

    return render_template('homepage.html', recommended_tracks=recommended_tracks, playlists=playlists, newsongs=newsongs)

@app.route('/songview/<int:track_id>', methods=['GET', 'POST'])
def songview(track_id):
    selected_track = song.query.get(track_id)
    song_url = selected_track.song_url
    if request.method == 'POST':
        
        searchh= request.form.get('search_query')
        if searchh is not None:
            song_match = song.query.filter_by(track=searchh).first()
            if song_match:
                return redirect(url_for('songview', track_id=song_match.id))
        
        return "listning functionality"

    return render_template('songview.html', song={'name': selected_track.track, 'creator': selected_track.creator, 'lyrics': selected_track.lyrics}, song_url=song_url,)

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        creator = request.form['artist']
        lyrics = request.form['lyrics']
        

        existing_song = song.query.filter(song.track==title).first()

        if existing_song is not None:
            return render_template('upload.html', message='Song already registered! Make original content or you may get copyrighted!')

        new_song = song(track=title, creator=creator, lyrics=lyrics)
        db.session.add(new_song)
        db.session.commit()

        session['track'] = title
        session['id'] = new_song.id

        return render_template('upload.html', message='Successfully registered your Song! It will be reviewed by admins to check for content policies.')
    

    return render_template('upload.html')



@app.route('/creatorreg', methods=['POST', 'GET'])
def creatorreg():
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice == 'yes':
            return redirect('/creatorkickstart')
        elif choice == 'no':
            return redirect('/homepage')

    return render_template('creatorregistration.html')

@app.route('/creatorkickstart', methods=['POST','GET'])
def creatorkickstart():
    return render_template('creatorkickstart.html')

@app.route('/admindashboard', methods=['POST','GET'])
def admindashboard():
    data = {
        'Months': ['October', 'November'],
        'Total Users': [350, 1049]
    }

    firstfig = px.line(data, x='Months', y='Total Users', title='App Usage Statistics')
    firstfig.update_layout(margin=dict(t=50, b=0, l=0, r=0), width=200, height=200)

    line_graph = pi.to_html(firstfig, full_html=False)

    data_pie = {
        'Category': ['User', 'Creator'],
        'Count': [1024, 25],
    }
    secondfig_pie = px.pie(data_pie, names='Category', values='Count', title='User vs Creator Ratio')

    secondfig_pie.update_layout(margin=dict(t=50, b=0, l=0, r=0), width=200, height=200)
    pie_graph = pi.to_html(secondfig_pie, full_html=False)

    return render_template('admindashboard.html', line_graph=line_graph, pie_graph=pie_graph)

@app.route('/alltracks', methods=['GET', 'POST'])
def alltracks():
    if request.method == 'POST':
        if 'delete' in request.form:
            song_id_to_delete = request.form.get('song_to_delete')
            if song_id_to_delete:
                song_to_delete = song.query.get(song_id_to_delete)
                if song_to_delete:
                    db.session.delete(song_to_delete)
                    db.session.commit()

        else:
            track = request.form.get('track')
            creator = request.form.get('creator')

            new_song = song(track=track, creator=creator)
            db.session.add(new_song)
            db.session.commit()

    songs = song.query.all()
    return render_template('alltracks.html', songs=songs)

@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit(song_id):
    selected_song = song.query.get(song_id)

    if request.method == 'POST':
        new_title = request.form['new_title']
        new_creator = request.form['new_creator']
        new_lyrics = request.form['new_lyrics']

        selected_song.track = new_title
        selected_song.creator = new_creator
        selected_song.lyrics = new_lyrics
        db.session.commit()
        return redirect(url_for('creatordashboard'))

    return render_template('edit.html', selected_song=selected_song)

@app.route('/myplaylist', methods=['GET', 'POST'])
def myplaylist():
    print("Request method:", request.method)
    print("Form data:", request.form)

    all_songs = song.query.all()

    if request.method == 'POST':
        playlist_name = request.form.get('playlist_name')
        selected_song_ids = request.form.getlist('selected_songs[]')

        print("Playlist Name:", playlist_name)
        print("Selected Song IDs:", selected_song_ids)

        playlists = playlist(name=playlist_name)

        for song_id in selected_song_ids:
            Song = song.query.get(song_id)
            playlists.songs.append(Song)

        db.session.add(playlists)
        db.session.commit()

        print("playlist created successfuly")

        return redirect(url_for('homepage'))

    return render_template('myplaylist.html', all_songs=all_songs)

@app.route('/creatordashboard', methods=['GET', 'POST'])
def creatordashboard():
    newsongs = song.query.filter(song.id > 15).all()

    if request.method =='POST':
        if 'delete' in request.form:
            delete_song_id = request.form.get('song_to_delete')
            if delete_song_id is not None:
                song_to_delete = song.query.get(delete_song_id)
                if song_to_delete:
                    db.session.delete(song_to_delete)
                    db.session.commit()

                return redirect(url_for('creatordashboard'))
        elif 'edit' in request.form:
            edit_song_id = request.form.get('edit_song')
            if edit_song_id:
                return redirect(url_for('edit', song_id=edit_song_id))     
        
        #if 'edit' in request.form:
            #edit_song= request.form.get('edit_song')
            #return redirect(url_for('edit'))

    return render_template('creatordashboard.html', newsongs=newsongs)


#@app.route('/edit',methods=['POST','GET'])
#def edit():
 #return render_template('edit.html',new_song=edit_song)


if __name__ == "__main__":
    app.run(debug=True)
