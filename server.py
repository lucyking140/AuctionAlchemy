"""
Columbia COMS W4111.001 Introduction to Databases Project 1
Lucy King, October 2023
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort
import re #for regular expressions

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

global current_user
current_user = None

DATABASEURI = "postgresql://lk2936:378782@34.74.171.121/proj1part2"

engine = create_engine(DATABASEURI)

conn = engine.connect()

@app.before_request
def before_request():

  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):

  try:
    g.conn.close()
  except Exception as e:
    pass

#HOME PAGE
@app.route('/', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
def home():
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)

  return render_template("home.html", current_user = current_user)

#LOGIN PAGE
@app.route('/login/', methods=['POST', 'GET'])
@app.route('/login', methods=['POST', 'GET'])
def login():

  global current_user
  mess = None

  if request.method == 'POST':
      username = request.form['username']
      password = request.form['password']

      #query to make sure this username is in the database and that their password is correct
      cursor = g.conn.execute(text("SELECT password FROM Users WHERE username=:user"), {"user": username})
      g.conn.commit()

      pwd = None
      for result in cursor:
        pwd = result[0]  
      cursor.close()

      if pwd == None: #no user with that username
          mess = "Sorry, we don't recognize a user with that username! \nTry again or click \"Sign Up\""
      elif pwd != password:
          mess = "Sorry, incorrect password. Try again!"
      else: #username and password are all set
        current_user = username
        return render_template("home.html", current_user = current_user)

  return render_template("login.html", message = mess, current_user = current_user)

#NO USER LOGGED IN PAGE
@app.route('/login_home/', methods=['POST', 'GET'])
@app.route('/login_home', methods=['POST', 'GET'])
def login_home():
  return render_template("login_home.html", current_user = current_user)

#LOG OUT PAGE
@app.route('/logout/', methods=['POST', 'GET'])
@app.route('/logout', methods=['POST', 'GET'])
def logout():
  global current_user
  current_user = None
  return render_template("login_home.html", current_user = current_user)

#SIGN UP PAGE
@app.route('/signup/', methods=['POST', 'GET'])
@app.route('/signup', methods=['POST', 'GET'])
def signup():

  global current_user

  mess = None
  if request.method == 'POST':
      username = request.form['username']
      password = request.form['password']
      email = request.form['email']
      first_name = request.form['first_name']
      last_name = request.form['last_name']

      mess = "Sorry, "
      if len(username) < 8:
        mess += "Your username is too short.\n"

      if " " in username:
        mess += "Please don't include spaces in your username."

      if len(username) >= 300:
        mess += "Your username is too long, it must be less than 300 characters.\n"
      if len(first_name) >= 300:
        mess += "Your first name is too long, it must be less than 300 characters.\n"
      if len(last_name) >= 300:
        mess += "Your last name is too long, it must be less than 300 characters.\n"
      if len(password) >= 300:
        mess += "Your password is too long, it must be less than 300 characters.\n"
      if len(email) >= 300:
        mess += "Your email is too long, it must be less than 300 characters.\n"

      #check if username is unique among users
      cursor = g.conn.execute(text("SELECT username FROM Users WHERE username = :username"), {"username": username})
      g.conn.commit()
      users = []
      for result in cursor:
        users.append(result)
      if len(users) > 0: #there is already a user with that username
        mess += "This username is not avaliable.\n"
      cursor.close()

      #checking if email is unique among users
      cursor = g.conn.execute(text("SELECT email FROM Users WHERE email = :email"), {"email": email})
      g.conn.commit()
      users = []
      for result in cursor:
        users.append(result)
      if len(users) > 0: #there is already a user with that email
        mess += "It looks like there's already an account registered with this email.\n"
      cursor.close()

      if len(password) < 8:
        mess += "Your password is too short.\n"

      pattern = re.compile(r'.*\d+.*')
      if not pattern.match(password): #password does not contain a digit
        mess += "Your password must contain at least one number.\n"

      #checking email validity
      pattern = re.compile(r'.+@.+\..+') #r'.+@.+\..+'

      if not pattern.match(email):
        mess += "Your email must be a valid format.\n"
      
      #valid user!
      if mess == "Sorry, ":
        mess = None
        current_user = username

        #query to insert a new user into the user table
        cursor2 = g.conn.execute(text("INSERT INTO Users VALUES (:username, :pass, :email, :first, :last)"), {"username": username, "pass": password, "email": email, "first": first_name, "last": last_name})
        g.conn.commit()
        cursor.close()

        return render_template("home.html", current_user = current_user)
      else:
        mess += "Please try again!"


  return render_template("signup.html", message = mess, current_user = current_user)

#LIST OF ALL USER PROFILES
@app.route('/profiles/')
@app.route('/profiles')
def profiles():
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)
  cursor = g.conn.execute(text("SELECT username, first_name, last_name FROM Users"))
  g.conn.commit()
  users = []
  for result in cursor:
    users.append(result)
  cursor.close()

  return render_template("profiles.html", users = users, current_user = current_user)

#INDIVIDUAL USER PROFILE
@app.route('/profiles/<username>/')
@app.route('/profiles/<username>')
def profile_page(username):
  #need to return all likes for works, auctions, and artists -- three lists
  global current_user
  if current_user == None:
      print("reaching login_home case, aka no user is logged in")
      return render_template("login_home.html", current_user = current_user)
  #getting all of the user info
  cursor = g.conn.execute(text("SELECT username, first_name, last_name FROM Users WHERE username = :username"), {"username": username})
  g.conn.commit()
  user = None
  for result in cursor:
    user = result
  cursor.close()

  #followed artists
  cursor = g.conn.execute(text("SELECT A.aid, A.first_name, A.last_name, A.birth_year, A.death_year, A.country_of_birth FROM Artist A, Follows_Artist F WHERE F.username = :username AND F.aid = A.aid"), {"username": username})
  g.conn.commit()
  followed_artists = []
  for result in cursor:
    followed_artists.append(result)
  cursor.close()

  #liked works
  cursor = g.conn.execute(text("SELECT A.first_name, A.last_name, W.title, W.year_created, W.aid FROM Artist A, Likes_Work_Of_Art W WHERE W.username = :username AND W.aid = A.aid"), {"username": username})
  g.conn.commit()
  liked_works = []
  for result in cursor:
    liked_works.append(result)
  cursor.close()

  #followed auctions
  cursor = g.conn.execute(text("SELECT F.title, F.date, F.house_name FROM Follows_Auction F WHERE F.username = :username"), {"username": username})
  g.conn.commit()
  followed_auctions = []
  for result in cursor:
    followed_auctions.append(result)
  cursor.close()

  #followed auction HOUSE
  cursor = g.conn.execute(text("SELECT F.house_name FROM Follows_Auction_House F WHERE F.username = :username"), {"username": username})
  g.conn.commit()
  followed_houses = []
  for result in cursor:
    followed_houses.append(result)
  cursor.close()

  #followed movements
  cursor = g.conn.execute(text("SELECT F.mvmt_name, M.start1, M.end1 FROM Likes_Movement F JOIN Movement M ON F.mvmt_name = M.name WHERE F.username = :username"), {"username": username})
  g.conn.commit()
  followed_mvmts = []
  for result in cursor:
    followed_mvmts.append(result)
  cursor.close()

  #followed regions
  cursor = g.conn.execute(text("SELECT F.region_name FROM Likes_Region F WHERE F.username = :username"), {"username": username})
  g.conn.commit()
  followed_regions = []
  for result in cursor:
    followed_regions.append(result)
  cursor.close()

  return render_template("profile_template.html", user = user, current_user = current_user, liked_works = liked_works, followed_artists = followed_artists, followed_auctions = followed_auctions, followed_houses = followed_houses, followed_mvmts=followed_mvmts, followed_regions=followed_regions)

#LIST ALL AUCTION HOUSES
@app.route('/auctionHouses/')
@app.route('/auctionHouses')
def auctionHouses():

  #user auth
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)
  
  #getting all houses
  cursor = g.conn.execute(text("SELECT name FROM Auction_House"))
  g.conn.commit()
  houses = []
  for result in cursor:
    houses.append(result)
  cursor.close()
  return render_template("auctionHouses.html", houses = houses, current_user = current_user)

#LIST INDIVIDUAL AUCTION HOUSES
@app.route('/auctionHouses/<name>/', methods = ['POST', 'GET'])
@app.route('/auctionHouses/<name>', methods = ['POST', 'GET'])
def auctionHouse_page(name):

  #NEED: all info, cumulative follows, and a follows button like above

  #checking user auth
  global current_user
  if current_user == None:
      print("reaching login_home case, aka no user is logged in")
      return render_template("login_home.html", current_user = current_user)
  
  #getting all of the auction house info
  cursor = g.conn.execute(text("SELECT * FROM Auction_House WHERE name = :name"), {"name": name})
  g.conn.commit()
  auctionHouse = None
  for result in cursor:
    auctionHouse = result
  cursor.close()
  #getting cumulative follows
  cursor = g.conn.execute(text("SELECT COUNT(*) FROM Follows_Auction_House WHERE house_name = :name"), {"name": name})
  g.conn.commit()

  likes = []
  for result in cursor:
    likes.append(result)
  cursor.close()

  ##################
  #GETTING "MOST POPULAR" DESCRIPTIONS
  #MOVEMENT
  cursorMvmt = g.conn.execute(text("SELECT M.name_movement, COUNT(*) as count FROM Auction_Focuses_On_Movement M WHERE M.name_auction_house = :house GROUP BY M.name_movement ORDER BY count DESC LIMIT 3"), {"house":name})
  g.conn.commit()
  topMoves = []
  for result in cursorMvmt:
    topMoves.append(result)
  cursorMvmt.close()
  #REGION
  cursorReg = g.conn.execute(text("SELECT M.name_region, COUNT(*) as count FROM Auction_Focuses_On_Region M WHERE M.name_auction_house = :name GROUP BY M.name_region ORDER BY count DESC LIMIT 3"), {"name":name})
  g.conn.commit()
  topRegions = []
  for result in cursorReg:
    topRegions.append(result)
  cursorReg.close()

  #ARTIST
  cursorReg = g.conn.execute(text("SELECT A.aid, A.first_name, A.last_name, COUNT(*) as count FROM Sold_In S JOIN Artist A ON S.aid = A.aid WHERE S.house_name = :name GROUP BY A.aid ORDER BY count DESC LIMIT 3"), {"name":name})
  g.conn.commit()
  topArtists = []
  for result in cursorReg:
    topArtists.append(result)
  cursorReg.close()

  ################
  #getting all auctions from that house
  cursorReg = g.conn.execute(text("SELECT * FROM Auction_By WHERE house_name = :name"), {"name":name})
  g.conn.commit()
  auctions = []
  for result in cursorReg:
    auctions.append(result)
  cursorReg.close()

  ################
  #checking for "Likes" and adding the like if it is there

  button = True
  # case where the user has already liked the post
  cursor = g.conn.execute(text("SELECT * FROM Follows_Auction_House WHERE username=:user AND house_name=:name"), {"user": current_user, "name": name})
  g.conn.commit()

  results = []
  for result in cursor:
    results.append(result)
  cursor.close()
  if len(results) > 0: #this user has already liked this work
    button = False
    if request.method == 'POST' and request.form['Un_follow'] == "Unfollow":
      print("reached unfollow case")
      cursor = g.conn.execute(text("DELETE FROM Follows_Auction_House WHERE username = :username AND house_name=:name"), {"username": current_user, "name": name})
      g.conn.commit()
      button = True
  else:
    #only want to add the user if it's not already there
    if request.method == 'POST' and request.form['Un_follow'] == "Follow":
      print("reachinf follow case")
      cursor = g.conn.execute(text("INSERT INTO Follows_Auction_House VALUES (:username, :name)"), {"username": current_user, "name": name})
      g.conn.commit()
      button = False
  cursor.close()
  return render_template("auctionHouse_template.html", house = auctionHouse, button=button, likes=likes, current_user=current_user, topMoves = topMoves, topRegions = topRegions, auctions = auctions, topArtists = topArtists)

#RECOMMENDATIONS
@app.route('/recommendations/<username>/')
@app.route('/recommendations/<username>')
def recommendations(username):

  #checking user auth
  global current_user
  if current_user == None:
      print("reaching login_home case, aka no user is logged in")
      return render_template("login_home.html", current_user = current_user)

  """
  What to base recommendations on:
  - get the most popular region, artist, and movement of liked works --> group by clauses
  - for every work in liked_works with a distinct artist:
    - choose two other works by that artist that are NOT already liked
  - same for auctions -- choose one other auction that has the same movemetn and one with the same region
  - more complex:Get two more artists for every artist liked that have the same most popular movement/region
  """

  #getting current user's first and last name
  cursor = g.conn.execute(text("SELECT first_name, last_name FROM Users WHERE username=:user"), {"user": username})
  g.conn.commit()

  user = []
  for result in cursor:
    user.append(result)
  user = user[0][0] + " " + user[0][1] #don't ahve to nullcheck this because we require a user to have a first and last name
  cursor.close()

  #getting favorite movement, region, and artist based on their liked works
  #movement:
  cursor = g.conn.execute(text("SELECT M.mvmt_name, COUNT(*) AS count FROM Likes_Work_Of_Art L NATURAL JOIN Work_Part_Of_Movement M WHERE L.username=:user GROUP BY M.mvmt_name ORDER BY count DESC LIMIT 1"), {"user": current_user})
  g.conn.commit()

  movement = []
  for result in cursor:
    movement.append(result)
  if movement:
    movement = movement[0][0]
  cursor.close()
  #see below for region
  if not movement:
    cursor = g.conn.execute(text("SELECT mvmt_name FROM Likes_Movement WHERE username = :user LIMIT 1"), {"user": current_user})
    g.conn.commit()

    movement = []
    for result in cursor:
      movement.append(result)
    if movement:
      movement = movement[0][0]
    cursor.close()
  #rregion 
  cursor = g.conn.execute(text("SELECT M.region_name, COUNT(*) AS count FROM Likes_Work_Of_Art L NATURAL JOIN Work_Part_Of_Region M WHERE L.username=:user GROUP BY M.region_name ORDER BY count DESC LIMIT 1"), {"user": current_user})
  g.conn.commit()

  region = []
  for result in cursor:
    region.append(result)
  if region:
    region = region[0][0]
  cursor.close()

  #defaulting to using a random liked region if there's no "favorite" region from the liked works of art
  if not region:
    cursor = g.conn.execute(text("SELECT region_name FROM Likes_Region WHERE username = :user LIMIT 1"), {"user": current_user})
    g.conn.commit()

    region = []
    for result in cursor:
      region.append(result)
    if region:
      region = region[0][0]
    cursor.close()
  #artist
  cursor = g.conn.execute(text("SELECT aid, COUNT(*) AS count FROM Likes_Work_Of_Art WHERE username=:user GROUP BY aid ORDER BY count DESC LIMIT 1"), {"user": current_user})
  g.conn.commit()

  aid = []
  artist = []
  for result in cursor:
    aid = result[0]
  cursor.close()
  #using a random followed artist if no liked works
  if not aid:
    cursor = g.conn.execute(text("SELECT aid FROM Follows_Artist WHERE username=:user LIMIT 1"), {"user": current_user})
    g.conn.commit()

    aid = []
    artist = []
    for result in cursor:
      aid = result[0]
    cursor.close()
  #getting the name of the favorite artist from their aid
  if aid:
    cursor = g.conn.execute(text("SELECT first_name, last_name FROM Artist WHERE aid = :aid"), {"aid": aid})
    g.conn.commit()

    artist = []
    for result in cursor:
      first = "" if not result[0] else result[0]
      last = "" if not result[1] else result[1]
      artist.append(str(first + " " + last))
    cursor.close()

  #getting two additional works for each of these categories
  works = []
  moveQuery = ""
  regQuery = ""
  artQuery = ""
  queryDict = {"aid": aid, "user": current_user, "move": movement, "region": region}
  #works from artist
  if aid:
    artQuery = "SELECT A.aid, A.first_name, A.last_name, W.title, W.year_created FROM Work_Of_Art_By W JOIN Artist A ON A.aid = W.aid WHERE A.aid = :aid AND (W.aid, W.title, W.year_created) NOT IN (SELECT aid, title, year_created FROM Likes_Work_Of_Art WHERE username = :user) LIMIT 2"
    cursor = g.conn.execute(text(artQuery), queryDict)
    g.conn.commit()

    for result in cursor:
      works.append(result)
    cursor.close()
    print("Works gotten from fav artist: ", works)

  #works from movement
  if movement:
    moveQuery = "SELECT A.aid, A.first_name, A.last_name, M.title, M.year_created FROM Work_Part_Of_Movement M JOIN Artist A ON A.aid = M.aid WHERE M.mvmt_name = :move AND (A.aid, M.title, M.year_created) NOT IN (SELECT aid, title, year_created FROM Likes_Work_Of_Art WHERE username = :user)"
    if aid:
      #adding not in the literal clause from above with the artists
      moveQuery += " AND (M.aid, A.first_name, A.last_name, M.title, M.year_created) NOT IN (" + artQuery + ")"
    moveQuery += " LIMIT 2"
    cursor = g.conn.execute(text(moveQuery), queryDict)
    g.conn.commit()

    for result in cursor:
      works.append(result)
    cursor.close()
    print("works after adding art from fave move: ", works)
  #works from regoin
  print("REGION: ", region)
  if region:
    regQuery = "SELECT A.aid, A.first_name, A.last_name, R.title, R.year_created FROM Work_Part_Of_Region R JOIN Artist A ON A.aid = R.aid WHERE R.region_name = :region AND (A.aid, R.title, R.year_created) NOT IN (SELECT aid, title, year_created FROM Likes_Work_Of_Art WHERE username = :user)"
    if aid:
      #making sure it's not in the artist 2
      regQuery += " AND (A.aid, A.first_name, A.last_name, R.title, R.year_created) NOT IN (" + artQuery + ")"
    if movement:
      regQuery += " AND (A.aid, A.first_name, A.last_name, R.title, R.year_created) NOT IN (" + moveQuery + ")" #this may or may not include the artist subquery here
    regQuery += " LIMIT 2"
    cursor = g.conn.execute(text(regQuery), queryDict)
    g.conn.commit()

    for result in cursor:
      works.append(result)
    cursor.close()
    print("works after adding fave regoin: ", works)

  #######################
  
  #getting one additional AUCTIONS for each of these categories
  auctions = []

  #works from movement
  if movement:
    queryDict = {"user": current_user, "move": movement}
    #auctions that have the same movement but are not already liked
    query = "SELECT title, date, name_auction_house FROM Auction_Focuses_On_Movement WHERE name_movement = :move AND (title, date, name_auction_house) NOT IN (SELECT title, date, house_name FROM Follows_Auction WHERE username=:user)"
    query += " LIMIT 2"
    cursor = g.conn.execute(text(query), queryDict)
    g.conn.commit()

    for result in cursor:
      auctions.append(result)
    cursor.close()
    print("auctions after adding AUCTIONS from fave move: ", auctions)
  #works from regoin
  if region:
    queryDict = {"user": current_user, "region": region}
    #getting list of all auctions with same region that have not been liked
    query = "SELECT title, date, name_auction_house FROM Auction_Focuses_On_Region WHERE name_region = :region AND (title, date, name_auction_house) NOT IN (SELECT title, date, house_name FROM Follows_Auction WHERE username=:user)"

    if movement:
      #copy-pasted from above, 
      query += " AND (title, date, name_auction_house) NOT IN (SELECT title, date, name_auction_house FROM Auction_Focuses_On_Movement WHERE name_movement = :move AND (title, date, name_auction_house) NOT IN (SELECT title, date, house_name FROM Follows_Auction WHERE username=:user) LIMIT 2)"
      queryDict["move"] = movement
    query += " LIMIT 2"
    cursor = g.conn.execute(text(query), queryDict)
    g.conn.commit()

    for result in cursor:
      auctions.append(result)
    cursor.close()
    print("auctions after adding fave regoin: ", auctions)
  #works from fav artist
  if aid:
    queryDict = {"user": current_user, "aid": aid, "move": movement, "region": region}
    query = "SELECT title_auction, date, house_name, COUNT(aid) as count FROM Sold_In WHERE aid = :aid AND (title_auction, date, house_name) NOT IN (SELECT title, date, house_name FROM Follows_Auction WHERE username=:user)"
    if movement and region:
        #literally just the two statements above appended
        query += " AND (title_auction, date, house_name) NOT IN (SELECT title, date, name_auction_house FROM Auction_Focuses_On_Region WHERE name_region = :region AND (title, date, name_auction_house) NOT IN (SELECT title, date, house_name FROM Follows_Auction WHERE username=:user) LIMIT 2) AND (title_auction, date, house_name) NOT IN (SELECT title, date, name_auction_house FROM Auction_Focuses_On_Movement WHERE name_movement = :move AND (title, date, name_auction_house) NOT IN (SELECT title, date, house_name FROM Follows_Auction WHERE username=:user) LIMIT 2)"
    elif region:
        query += " AND (title_auction, date, house_name) NOT IN (SELECT title, date, name_auction_house FROM Auction_Focuses_On_Region WHERE name_region = :region AND (title, date, name_auction_house) NOT IN (SELECT title, date, house_name FROM Follows_Auction WHERE username=:user) LIMIT 2)"
    elif movement:
        query += " AND (title_auction, date, house_name) NOT IN (SELECT title, date, name_auction_house FROM Auction_Focuses_On_Movement WHERE name_movement = :move AND (title, date, name_auction_house) NOT IN (SELECT title, date, house_name FROM Follows_Auction WHERE username=:user) LIMIT 2)"
    query += " GROUP BY title_auction, house_name, date ORDER BY count DESC NULLS LAST LIMIT 2"
    
    cursor = g.conn.execute(text(query), queryDict)
    g.conn.commit()

    for result in cursor:
      auctions.append(result)
    cursor.close()
    print("auctions after adding AUCTIONS from fave artist: ", auctions)

  #######################

  message = None
  if not region and not movement and not aid: #no likes
    message = "Sorry, it looks like you haven't liked enough items yet! Keep looking and we'll update this page."

  elif not works: #have likes but no works have been recommended
    message = "Sorry, it looks like you've already liked all of the works in the areas that you've liked, so we can't provide any recommendations right now."

  return render_template("recommendations.html", region = region, movement = movement, current_user = current_user, artist = artist, works = works, message = message, user=user, auctions=auctions)

#LIST ALL AUCTIONS
@app.route('/auctions/', methods = ['POST', 'GET'])
@app.route('/auctions', methods = ['POST', 'GET'])
def auctions():
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)

  query = "SELECT title, date, house_name FROM Auction_By"
  queryDict = {}

  #getting all titles and all locations for search options!
  cursor = g.conn.execute(text("SELECT DISTINCT title FROM Auction_By"))
  g.conn.commit()
  titles=[]
  for result in cursor:
    titles.append(result)
  cursor.close()

  titles.append((""))

  cursor = g.conn.execute(text("SELECT DISTINCT location FROM Auction_By"))
  g.conn.commit()
  locations=[]
  for result in cursor:
    locations.append(result)
  cursor.close()

  locations.append((""))

  #Search by auction name and location
  if request.method == "POST":
    auction_title = request.form['title']
    location = request.form['location']
    if auction_title:
      query += " WHERE title = :title"
      queryDict["title"] = auction_title
    if location:
      if auction_title:
        query += " AND location = :location"
      else:
        query += " WHERE location = :location"
      queryDict["location"] = location
  
  cursor = g.conn.execute(text(query), queryDict)
  g.conn.commit()

  titles_and_dates = [] #this also includes house name, didn't want to rename it
  for result in cursor:
    #print(result)
    titles_and_dates.append(result)  
  context = dict(data = titles_and_dates)
  cursor.close()
  message = None
  if not titles_and_dates: #no results
    message = "Sorry, there are no auctions that match those search results!"

  return render_template("auctions.html", **context, current_user = current_user, message = message, titles=titles, locations=locations)

#LIST INDIVIDUAL AUCTION
@app.route('/auctions/<title>/<date>/<house>/', methods = ['POST', 'GET'])
@app.route('/auctions/<title>/<date>/<house>',  methods = ['POST', 'GET'])
def auction_page(title, date, house):
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)

  #this is just getting all the info from this specific auction
  cursor2 = g.conn.execute(text("SELECT * FROM Auction_By WHERE title=:title AND date=:date"), {"title": title, "date": date})
  g.conn.commit()
  for cursor1 in cursor2:
    auction = {"title": cursor1[0],	"date": cursor1[1],"location": cursor1[2],"total_sales": cursor1[3],"house_name": cursor1[4]}  
  cursor2.close()
  #getting most popular artist, movement, and region featured in the auction

  #ARTIST
  cursorArtist = g.conn.execute(text("SELECT aid, COUNT(*) AS count FROM Sold_In WHERE title_auction = :auction AND house_name = :house AND date=:date GROUP BY aid ORDER BY count DESC LIMIT 3"), {"auction": auction['title'], "house": auction['house_name'], "date":auction['date']})
  g.conn.commit()
  topAids = []
  for result in cursorArtist:
    topAids.append(result)
  cursorArtist.close()
  #now getting the artist name from the aid
  topArtists=[]
  for aid, count in topAids:
    cursorName = g.conn.execute(text("SELECT first_name, last_name FROM Artist WHERE aid=:aid"), {"aid": aid})
    g.conn.commit()
    for result in cursorName:
      first = "" if not result[0] else result[0]
      last = ""if not result[1] else result[1]
      topArtists.append((str(first + " " + last), count))
    cursorName.close()
  #MOVEMENT
  cursorMvmt = g.conn.execute(text("SELECT M.mvmt_name, COUNT(*) as count FROM Work_Part_Of_Movement M, Sold_In S WHERE M.title = S.title_work AND M.aid = S.aid AND M.year_created = S.year_created AND S.title_auction = :auction AND S.house_name = :house AND S.date = :date GROUP BY M.mvmt_name ORDER BY count DESC LIMIT 3"), {"auction": auction['title'], "house": auction['house_name'], "date":auction['date']})
  g.conn.commit()
  topMoves = []
  for result in cursorMvmt:
    topMoves.append(result)
  cursorMvmt.close()
  #REGION
  cursorReg = g.conn.execute(text("SELECT M.region_name, COUNT(*) as count FROM Work_Part_Of_Region M, Sold_In S WHERE M.title = S.title_work AND M.aid = S.aid AND M.year_created = S.year_created AND S.title_auction = :auction AND S.house_name = :house AND S.date = :date GROUP BY M.region_name ORDER BY count DESC LIMIT 3"), {"auction": auction['title'], "house": auction['house_name'], "date":auction['date']})
  g.conn.commit()
  topRegions = []
  for result in cursorReg:
    topRegions.append(result)
  cursorReg.close()

  #getting info for all of the works sold in the auction
  cursor = g.conn.execute(text("SELECT S.title_work, S.year_created, S.aid, A.first_name, A.last_name FROM Sold_In S, Artist A WHERE S.aid = A.aid AND S.title_auction=:title AND S.date=:date"), {"title": title, "date": date})
  g.conn.commit()
  
  titles = []
  for result in cursor:
    print(result)
    titles.append(result)  
  context = dict(data = titles)
  cursor.close()

  #getting cumulative follows
  cursor = g.conn.execute(text("SELECT COUNT(*) FROM Follows_Auction WHERE house_name = :house AND date=:date AND title=:title"), {"house": house, "title": title, "date": date})
  g.conn.commit()

  likes = []
  for result in cursor:
    likes.append(result)
  cursor.close()
  #checking for "Likes" and adding the like if it is there
  button = True
  # case where the user has already liked the post
  cursor = g.conn.execute(text("SELECT * FROM Follows_Auction WHERE username=:user AND house_name = :house AND date=:date AND title=:title"), {"user": current_user, "house": house, "title": title, "date": date})
  g.conn.commit()

  results = []
  for result in cursor:
    results.append(result)
  cursor.close()
  if len(results) > 0: #this user has already liked this work
    button = False
    if request.method == 'POST' and request.form['Un_follow'] == "Unfollow":
      print("reached unfollow case")
      cursor = g.conn.execute(text("DELETE FROM Follows_Auction WHERE username = :user AND title=:title AND date=:date AND house_name=:house"), {"user": current_user, "house": house, "title": title, "date": date})
      g.conn.commit()
      button = True
  else:
    #only want to add the user if it's not already there
    if request.method == 'POST' and request.form['Un_follow'] == "Follow":
      print("reachinf follow case")
      cursor = g.conn.execute(text("INSERT INTO Follows_Auction VALUES (:user, :title, :date, :house)"), {"user": current_user, "house": house, "title": title, "date": date})
      g.conn.commit()
      button = False
  cursor.close()
  return render_template('auction_template.html', **context, auction = auction, current_user = current_user, topArtists = topArtists, topMovements = topMoves, topRegions = topRegions, likes=likes[0], button=button)

#LIST ALL REGIONS
@app.route('/regions/')
@app.route('/regions')
def regions():
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)
  
  cursor = g.conn.execute(text("SELECT name FROM World_Region"))
  g.conn.commit()

  regions = [] #this also includes house name, didn't want to rename it
  for result in cursor:
    #print(result)
    regions.append(result)  
  context = dict(data = regions)
  cursor.close()
  return render_template("regions.html", **context, current_user = current_user)

#LIST INDIVIDUAL REGION
@app.route('/regions/<name>/', methods = ['POST', 'GET'])
@app.route('/regions/<name>', methods = ['POST', 'GET'])
def region_page(name):
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)

  #getting info for all of the works sold in the auction
  cursor = g.conn.execute(text("SELECT * FROM Work_Part_Of_Region W NATURAL JOIN Artist A WHERE region_name = :region"), {"region": name})
  g.conn.commit()
  
  works = []
  for result in cursor:
    works.append(result)  
  context = dict(data = works)
  cursor.close()
  #getting cumulative follows
  cursor = g.conn.execute(text("SELECT COUNT(*) FROM Likes_Region WHERE region_name = :name"), {"name": name})
  g.conn.commit()

  likes = []
  for result in cursor:
    likes.append(result)
  cursor.close()

  #checking for "Likes" and adding the like if it is there
  button = True
  # case where the user has already liked the post
  cursor = g.conn.execute(text("SELECT * FROM Likes_Region WHERE username=:user AND region_name=:name"), {"user": current_user, "name":name})
  g.conn.commit()

  results = []
  for result in cursor:
    results.append(result)
  cursor.close()
  if len(results) > 0: #this user has already liked this work
    button = False
    if request.method == 'POST' and request.form['Un_follow'] == "Unfollow":
      print("reached unfollow case")
      cursor = g.conn.execute(text("DELETE FROM Likes_Region WHERE username = :user AND region_name=:name"), {"user": current_user, "name":name})
      g.conn.commit()
      button = True
  else:
    #only want to add the user if it's not already there
    if request.method == 'POST' and request.form['Un_follow'] == "Follow":
      print("reachinf follow case")
      cursor = g.conn.execute(text("INSERT INTO Likes_Region VALUES (:user, :name)"), {"user": current_user, "name":name})
      g.conn.commit()
      button = False
  return render_template('region_template.html', **context, current_user=current_user, likes=likes, button=button, name=name)

#LIST ALL MOVEMENTS
@app.route('/movements/')
@app.route('/movements')
def movements():
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)
  
  cursor = g.conn.execute(text("SELECT * FROM Movement"))
  g.conn.commit()

  regions = [] #this also includes house name, didn't want to rename it
  for result in cursor:
    #print(result)
    regions.append(result)  
  context = dict(data = regions)
  cursor.close()
  return render_template("movements.html", **context, current_user = current_user)

#LIST INDIVIDUAL MOVEMENT
@app.route('/movements/<name>/', methods = ['POST', 'GET'])
@app.route('/movemenst/<name>', methods = ['POST', 'GET'])
def movement_page(name):
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)

  #getting info on the current movement
  cursor = g.conn.execute(text("SELECT * FROM Movement WHERE name = :move"), {"move": name})
  g.conn.commit()
  
  info = []
  for result in cursor:
    info.append(result)  
  info = dict(inform = info)
  cursor.close()
  #getting info for all of the works sold in the auction
  cursor = g.conn.execute(text("SELECT * FROM Work_Part_Of_Movement W NATURAL JOIN Artist A WHERE mvmt_name = :move"), {"move": name})
  g.conn.commit()
  
  works = []
  for result in cursor:
    works.append(result)  
  context = dict(data = works)
  cursor.close()
  #getting cumulative follows
  cursor = g.conn.execute(text("SELECT COUNT(*) FROM Likes_Movement WHERE mvmt_name = :name"), {"name": name})
  g.conn.commit()

  likes = []
  for result in cursor:
    likes.append(result)
  cursor.close()

  #checking for "Likes" and adding the like if it is there
  button = True
  # case where the user has already liked the post
  cursor = g.conn.execute(text("SELECT * FROM Likes_Movement WHERE username=:user AND mvmt_name = :name"), {"user": current_user, "name": name})
  g.conn.commit()

  results = []
  for result in cursor:
    results.append(result)
  cursor.close()
  if len(results) > 0: #this user has already liked this work
    button = False
    if request.method == 'POST' and request.form['Un_follow'] == "Unfollow":
      print("reached unfollow case")
      cursor = g.conn.execute(text("DELETE FROM Likes_Movement WHERE username = :user AND mvmt_name=:name"), {"user": current_user, "name": name})
      g.conn.commit()
      button = True
  else:
    #only want to add the user if it's not already there
    if request.method == 'POST' and request.form['Un_follow'] == "Follow":
      print("reachinf follow case")
      cursor = g.conn.execute(text("INSERT INTO Likes_Movement VALUES (:user, :name)"), {"user": current_user, "name":name})
      g.conn.commit()
      button = False
  cursor.close()
  return render_template('movement_template.html', **context, current_user=current_user, likes=likes, button=button, name=name, **info)


#LISTS ALL ARTISTS
@app.route('/artists/', methods=['POST', 'GET'])
@app.route('/artists', methods=['POST', 'GET'])
def artists():

  #checking user auth
  global current_user
  if current_user == None:
    return render_template("login_home.html", current_user = current_user)

  #getting all artists
  query = "SELECT * FROM Artist"
  if request.method == 'POST': #sorting by popularity
    print("reaching order_by case!")
    #basically just including only the artist attributes, just ordered by the number of follows
    #left join to include all of the artists that have no follows 
    query = "SELECT A.aid, A.first_name, A.last_name, A.death_year, A.birth_year, A.country_of_birth, COUNT(*) as count FROM Artist A LEFT JOIN Follows_Artist F ON F.aid = A.aid GROUP BY A.aid, A.first_name, A.last_name, A.death_year, A.birth_year, A.country_of_birth ORDER BY count DESC NULLS LAST"
  cursor = g.conn.execute(text(query))
  g.conn.commit()

  # Indexing result by column number
  artists = []
  for result in cursor:
    #print(result)
    artists.append(result)  
  context = dict(data = artists)
  print(context)
  cursor.close()
  return render_template("artists.html", **context, current_user=current_user)

#LISTS INDIVIDUAL ARTIST
@app.route('/artists/<aid>/', methods=['POST', 'GET'])
@app.route('/artists/<aid>', methods=['POST', 'GET'])
def artist_page(aid):

  #checking user auth
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)

  #getting all of the artist info

  cursor = g.conn.execute(text("SELECT * FROM Artist WHERE aid=:aid"), {"aid": aid})
  g.conn.commit()

  artist = []
  for result in cursor:
    artist.append(result)
  cursor.close()
  #cumulative artist likes
  cursor = g.conn.execute(text("SELECT COUNT(*) FROM Follows_Artist WHERE aid=:aid"), {"aid": aid})
  g.conn.commit()

  likes = []
  for result in cursor:
    likes.append(result)
  cursor.close()
  """
  #following an artist
  button = True
  # case where the user has already liked the artist
  cursor = g.conn.execute(text("SELECT * FROM Follows_Artist WHERE username=:user AND aid=:aid"), {"user": current_user, "aid": aid})
  g.conn.commit()

  results = []
  for result in cursor:
    results.append(result)
  cursor.close()
  if len(results) > 0: #this user has already liked this work
    button = False
  else:
    #only want to add the user if it's not already there
    if request.method == 'POST':
      cursor = g.conn.execute(text("INSERT INTO Follows_Artist VALUES (:username, :aid)"), {"username": current_user, "aid": aid})
      g.conn.commit()
      button = False
      cursor.close()
  """
  #checking for "Likes" and adding the like if it is there
  button = True
  # case where the user has already liked the post
  cursor = g.conn.execute(text("SELECT * FROM Follows_Artist WHERE username=:user AND aid=:aid"), {"user": current_user, "aid": aid})
  g.conn.commit()

  results = []
  for result in cursor:
    results.append(result)
  cursor.close()
  if len(results) > 0: #this user has already liked this work
    button = False
    if request.method == 'POST' and request.form['Un_follow'] == "Unfollow":
      print("reached unfollow case")
      cursor = g.conn.execute(text("DELETE FROM Follows_Artist WHERE username = :user AND aid=:aid"), {"user": current_user, "aid": aid})
      g.conn.commit()
      button = True
  else:
    #only want to add the user if it's not already there
    if request.method == 'POST' and request.form['Un_follow'] == "Follow":
      print("reachinf follow case")
      cursor = g.conn.execute(text("INSERT INTO Follows_Artist VALUES (:username, :aid)"), {"username": current_user, "aid": aid})
      g.conn.commit()
      button = False
  cursor.close()
  return render_template("artist_template.html", button=button, current_user=current_user, artist=artist[0], likes = likes)

#LISTS INDIVIDUAL WORK
@app.route('/works/<title>/<year>/<aid>/', methods=['POST', 'GET'])
@app.route('/works/<title>/<year>/<aid>', methods=['POST', 'GET'])
def work_page(title, year, aid):
  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)

  #initial query to get sale price
  #now: get normal info, then run a separate query to get prices 
  # --> send prices and auction title/house/date to the work_page, which can be displayed as lines
  #cursor = g.conn.execute(text("SELECT W.title, W.year_created, W.medium, W.aid, S.sold_for, S.high_est, S.low_est FROM Work_Of_Art_By W, Sold_In S WHERE W.title = S.title_work AND W.aid = S.aid AND W.year_created = S.year_created AND W.title=:title AND W.year_created=:year AND W.aid=:aid"), {"title": title, "year": year, "aid": aid})
  
  #getting all work info
  cursor = g.conn.execute(text("SELECT W.title, W.year_created, W.medium, W.aid FROM Work_Of_Art_By W WHERE W.title=:title AND W.year_created=:year AND W.aid=:aid"), {"title": title, "year": year, "aid": aid})
  g.conn.commit()

  workInfo = []
  for result in cursor:
    workInfo.append(result)  
  context = dict(data = workInfo)
  cursor.close()

  #getting artist name
  cursor2 = g.conn.execute(text("SELECT first_name, last_name FROM Artist WHERE aid=:aid"), {"aid": aid})
  g.conn.commit()

  name = ""
  for result in cursor2:
    first = "" if not result[0] else result[0]
    last = "" if not result[1] else result[1]
    name = first + " "+ last
  artist_name = dict(name = name)  
  cursor2.close()

  #getting sales
  cursor = g.conn.execute(text("SELECT S.sold_for, S.high_est, S.low_est, S.title_auction, S.house_name, S.date FROM Work_Of_Art_By W, Sold_In S WHERE W.title = S.title_work AND W.aid = S.aid AND W.year_created = S.year_created AND W.title=:title AND W.year_created=:year AND W.aid=:aid"), {"title": title, "year": year, "aid": aid})
  g.conn.commit()

  saleInfo = []
  for result in cursor:
    saleInfo.append(result)  
  cursor.close()

  #cumulative likes
  cursor = g.conn.execute(text("SELECT COUNT(*) FROM Likes_Work_Of_Art WHERE title=:title AND aid=:aid AND year_created=:year"), {"aid": aid, "title": title, "year":year})
  g.conn.commit()

  likes = []
  for result in cursor:
    likes.append(result)
  cursor.close()
 
  #checking for "Likes" and adding the like if it is there
  button = True
  # case where the user has already liked the post
  cursor = g.conn.execute(text("SELECT * FROM Likes_Work_Of_Art WHERE username=:user AND title=:title AND aid=:aid AND year_created=:date"), {"user": current_user, "title": title, "aid":aid, "date":year})
  g.conn.commit()

  results = []
  for result in cursor:
    results.append(result)
  cursor.close()
  if len(results) > 0: #this user has already liked this work
    button = False
    if request.method == 'POST' and request.form['Un_follow'] == "Unfollow":
      print("reached unfollow case")
      cursor = g.conn.execute(text("DELETE FROM Likes_Work_Of_Art WHERE username = :user AND title=:name AND aid=:aid AND year_created=:year"), {"user": current_user, "name": title, "aid": aid, "year":year})
      g.conn.commit()
      button = True
  else:
    #only want to add the user if it's not already there
    if request.method == 'POST' and request.form['Un_follow'] == "Follow":
      print("reachinf follow case")
      cursor = g.conn.execute(text("INSERT INTO Likes_Work_Of_Art VALUES (:username, :aid, :title, :year_created)"), {"username": current_user, "aid": aid, "title": title, "year_created":year})
      g.conn.commit()
      button = False
  cursor.close()
  
  return render_template('work_template.html', **context, title=title, year=year, **artist_name, current_user = current_user, button = button, likes=likes, saleInfo = saleInfo)

#LISTS ALL WORKS
@app.route('/works/', methods=['POST', 'GET'])
@app.route('/works', methods=['POST', 'GET'])
def works():

  global current_user
  if current_user == None:
    print("reaching login_home case, aka no user is logged in")
    return render_template("login_home.html", current_user = current_user)

  #default query if no post requests
  query = "SELECT DISTINCT W.title, W.year_created, A.first_name, A.last_name, A.aid FROM Work_Of_Art_By W, Artist A WHERE A.aid = W.aid"
  queryDict = {}

  if request.method == 'POST':
        title = request.form['title']
        artist = request.form['artist']
        movement = request.form['movement']
        region = request.form['region']
        auction = request.form['auction']
        medium = request.form['medium']

        options = {'title': title, 'artist': artist, 'movement':movement, 'region':region, 'auction': auction, 'medium':medium}

        for key, val in options.items():
            if val != "":
                queryDict[key] = val

        print("INFO: ", queryDict)

        #this will be where we fill this in

        #currently just testing formatting of this query

        #S.title_work, S.year_created, A.first_name, A.last_name

        work_region_movement_artist = "SELECT * FROM Work_Part_Of_Region NATURAL JOIN Work_Part_Of_Movement NATURAL JOIN Artist NATURAL JOIN Work_Of_Art_By"
        
        query = "SELECT DISTINCT W.title, S.year_created, W.first_name, W.last_name, S.aid " + "FROM Sold_In S JOIN (" + work_region_movement_artist + ") W ON S.year_created=W.year_created AND S.aid=W.aid AND S.title_work = W.title"

        #adding search options
        #options = {'artist': artist, 'movement':movement, 'region':region, 'auction': auction}
        if options['artist']:
          artist = options['artist']
          first = ""
          last = ""
          for i in range(len(artist)):
            if artist[i] == " ":
              first = artist[:i]
              last = artist[i + 1:]
          if not first: #case w no last name
            first = artist
          print("artist first: ", first)
          print("artist last: ", last)
          query += " WHERE W.first_name = :first AND W.last_name = :last"
          queryDict["first"] = first
          queryDict["last"] = last
        if options['movement']:
          movement = options['movement']
          query += " AND " if query[len(query) - 1] == "t" else " WHERE " #adding and if we've already added a A WHERE
          query += "W.mvmt_name = :move"
          queryDict["move"] = movement
        if options['region']:
          region = options['region']
          print("prev where check in region, should be ve: ", query[len(query) - 2:len(query)])
          query += " AND " if query[len(query) - 1] == "t" or query[len(query) - 2:len(query)] == "ve" else " WHERE " #adding and if we've already added a A WHERE
          query += "W.region_name = :region"
          queryDict["region"] = region
        if options['auction']:
          auction = options['auction']
          query += " AND " if query[len(query) - 1] == "t" or query[len(query) - 2:len(query)] == "ve" or query[len(query)-1] == "n" else " WHERE " #adding and if we've already added a A WHERE
          query += "S.title_auction = :auction"
          queryDict["auction"] = auction
        if options['medium']:
          med = options['medium']
          query += " AND (" if query[len(query) - 1] == "t" or query[len(query) - 2:len(query)] == "ve" or query[len(query)-1] == "n" else " WHERE (" #adding and if we've already added a A WHERE
          querMed = []
          querMed.append(med + " " + "%")
          querMed.append(med + "," + "%")
          querMed.append(med)
          querMed.append("%" + " " + med)
          querMed.append("%" + " " + med + " " + "%")
          querMed.append("%" + " " + med + "," + "%")

          for phr in querMed:
            query += "W.medium LIKE '" + phr + "' OR "

          query += "W.medium LIKE '" + "%" + " " + med + "," + "%')"
          queryDict["medium"] = med
        if options['title']:
          title = options['title']
          query += " AND " if query[len(query) - 1] == "t" or query[len(query) - 2:len(query)] == "ve" or query[len(query)-1] == "n" or query[len(query)-1] == ")" else " WHERE " #adding and if we've already added a A WHERE
          query += "S.title_work = :title"
          queryDict["title"] = title

    #then need to decide the constraints and what table to pull from ... 
    #do a bool checker for which table we need, and join accordingly

  print("QUERY: ", query)
  #this is the query for ALL works. Only use this if no filters specified
  cursor = g.conn.execute(text(query), queryDict)
  g.conn.commit()

  # Indexing result by column number
  titleYearArtist = []
  for result in cursor:
    #print(result)
    titleYearArtist.append(result)  
  context = dict(data = titleYearArtist)
  cursor.close()

  #getting movements rq
  cursor = g.conn.execute(text("SELECT name FROM Movement"))
  g.conn.commit()

  movements = []
  for result in cursor:
    #print(result)
    movements.append(result[0])
  cursor.close()

  #getting regions
  cursor = g.conn.execute(text("SELECT name FROM World_Region"))
  g.conn.commit()

  regions = []
  for result in cursor:
    #print(result)
    regions.append(result[0])
  cursor.close()

  #getting artists
  cursor = g.conn.execute(text("SELECT first_name, last_name FROM Artist"))
  g.conn.commit()

  artists = []
  for result in cursor:
    #print(result)
    first = "" if not result[0] else result[0]
    last = ""if not result[1] else result[1]
    artists.append((str(first + " " + last)))
  cursor.close()

  #getting auctions
  cursor = g.conn.execute(text("SELECT DISTINCT title FROM Auction_By"))
  g.conn.commit()

  auctions = []
  for result in cursor:
    #print(result)
    auctions.append(str(result[0]))
  cursor.close()

  #gettting titles
  cursor = g.conn.execute(text("SELECT DISTINCT title FROM Work_Of_Art_By"))
  g.conn.commit()

  titles = []
  for result in cursor:
    #print(result)
    titles.append(str(result[0]))
  cursor.close()
  titles.append("")

  #getting mediums
  mediums = ["", "paper",  "panel", "canvas", "card",  "board", "bronze", "marble", "porcelain", "ceramic", "glass", "metal", "tin", "brass", "burlap", "wood", "masonite", "cardboard", "plaster", "linen", "iron"] 

  return render_template("works.html", **context, movements = movements, regions = regions, current_user = current_user, artists=artists, auctions = auctions, mediums = mediums, titles=titles)


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=True, threaded=threaded)

  run()
