from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
from twilio.rest import Client 
from werkzeug.exceptions import HTTPException

import requests

# NOTE: you must manually set API_KEY below using information retrieved from your IBM Cloud account.
API_KEY = "4pewzbYZOBMZuMhd1PDoWyHOx4J4oUGn6eZPiycEvdJJ"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
 API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}


app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '5005kruthi'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'log_mail' in request.form and 'pswd' in request.form:
        # Create variables for easy access
        log_mail = request.form['log_mail']
        pswd = request.form['pswd']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM register WHERE email = %s AND pswd = %s', (log_mail, pswd,))
        # Fetch one record and return result
        profile = cursor.fetchone()
        # If account exists in accounts table in out database
        if profile:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = profile['id']
            session['log_mail'] = profile['email']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect email/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('log_mail', None)
   # Redirect to login page
   return redirect(url_for('login')) 

@app.route('/getotp', methods=['GET', 'POST'])
def getotp():
    msg=''
    if request.method == 'POST' and 'phone' in request.form and 'uname' in request.form :
      # Create variables for easy access
      global phone,uname
      phone = request.form['phone'] 
      uname = request.form['uname'] 
      
      cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
      cursor.execute('SELECT * FROM registration WHERE phone= %s', (phone,))
      account = cursor.fetchone()
      if account:
          msg = 'Account already exists!'
      else:
          #cursor.execute('INSERT INTO registration VALUES (NULL, %s)', (phone,))
          #mysql.connection.commit() 
          try:
              account_sid ='ACf605690bd4d15edaf43560e3be75d622' 
              auth_token = '050436e3811cf120fa1b12f77fd0fae2' 
              client = Client(account_sid, auth_token) 
              verification = client.verify \
                               .v2 \
                               .services('VAf924698b5a809f7041269be39e245851') \
                               .verifications \
                               .create(to=phone, channel='sms') 
              if verification.status=='pending':
                  msg='OTP Sucessfully sent!' 
              else:
                  msg='Check Your Phone Number' 
          except Exception:
              msg='Enter Your PhoneNumber Correctly'
    return render_template('signup.html', msg=msg) 

    
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'otp' in request.form:
        # Create variables for easy access
        otp= request.form['otp']
        account_sid ='ACf605690bd4d15edaf43560e3be75d622'
        auth_token = '050436e3811cf120fa1b12f77fd0fae2'
        client = Client(account_sid, auth_token)

        verification_check = client.verify \
                                   .v2 \
                                   .services('VAf924698b5a809f7041269be39e245851') \
                                   .verification_checks \
                                   .create(to=phone, code=otp)

        if verification_check.status=='approved':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO registration VALUES (NULL, %s, %s)', (phone,uname,))
            mysql.connection.commit() 
            return redirect(url_for('profile'))
        else:
            msg = 'Incorrect OTP'

    # Show registration form with message (if any)
    return render_template('signup.html', msg=msg) 


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'pswd' in request.form and 'email' in request.form and 'location' in request.form and 'occupation' in request.form and 'con_pswd' in request.form:
        # Create variables for easy access
        username = request.form['username']
        email = request.form['email']
        location = request.form['location']
        occupation= request.form['occupation']
        con_pswd = request.form['con_pswd']
        pswd = request.form['pswd']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM register WHERE email = %s', (email,))
        register = cursor.fetchone()
        # If account exists show error and validation checks
        if register:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif pswd!=con_pswd:
            msg='Password did not Match'
        elif not username or not pswd or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO register VALUES (NULL, %s, %s, %s,%s,%s,%s,%s)', (username,email,location,occupation,pswd,con_pswd,phone,))
            mysql.connection.commit()
            msg = 'You have successfully registered!' 
            
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM register WHERE email = %s AND pswd = %s', (email, pswd,))
            # Fetch one record and return result
            profile = cursor.fetchone()
            # If account exists in accounts table in out database
            if profile:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = profile['id']
                session['log_mail'] = profile['email']
                # Redirect to home page
                return redirect(url_for('home'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('profile-page.html', msg=msg) 

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('popup.html')
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/review', methods=['GET', 'POST'])
def review():
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'review' in request.form:
        # Create variables for easy access
        review = request.form['review'] 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO feedback VALUES (NULL, %s)', (review,))
        mysql.connection.commit() 
        msg="Thank You for the valuable feedback!"
        return render_template('popup.html', msg=msg) 
    else:
        msg='Fill the form!'
        return render_template('popup.html', msg=msg) 
        
@app.route('/rate', methods=['GET', 'POST'])
def rate():    
    if request.method == 'POST' and 'rate' in request.form:
        # Create variables for easy access
        rate = request.form['rate'] 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO rate VALUES (NULL, %s)', (rate,))
        mysql.connection.commit() 
        msg="Thanks for Rating Us!"
        return render_template('popup.html', msg=msg)
    else:
        msg='Fill the form'
        return render_template('popup.html', msg=msg) 
        
@app.route('/resetotp', methods=['GET', 'POST'])
def resetotp(): 
    msg=''
    if request.method == 'POST' and 'mobile' in request.form:
      # Create variables for easy access
      global mobile
      mobile = request.form['mobile'] 
       
      cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
      cursor.execute('SELECT * FROM register WHERE phone= %s', (mobile,))
      account = cursor.fetchone()
      if account:
          try:
              account_sid ='AC5a17fbe4f1136a9420b131184eccf02f' 
              auth_token = '8976233f3e08dfdf8fc99946ceb3858c' 
              client = Client(account_sid, auth_token) 
              verification = client.verify \
                               .v2 \
                               .services('VA258829db0002722215f1024b3e94c64b') \
                               .verifications \
                               .create(to=mobile, channel='sms') 
              if verification.status=='pending':
                  msg='OTP Sucessfully sent!' 
              else:
                  msg='Check Your Phone Number' 
          except Exception:
              msg='Enter Your PhoneNumber Correctly' 
      else:
          msg='You dont Have an Account'
    return render_template('forgot.html', msg=msg) 

@app.route('/otpverify', methods=['GET', 'POST'])
def otpverify():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'otp' in request.form:
        # Create variables for easy access
        otp= request.form['otp']
        account_sid ='AC5a17fbe4f1136a9420b131184eccf02f'
        auth_token = '8976233f3e08dfdf8fc99946ceb3858c'
        client = Client(account_sid, auth_token)

        verification_check = client.verify \
                                   .v2 \
                                   .services('VA258829db0002722215f1024b3e94c64b') \
                                   .verification_checks \
                                   .create(to=mobile, code=otp)

        if verification_check.status=='approved':
            return redirect(url_for('setpswd'))
        else:
            msg = 'Incorrect OTP'

    # Show registration form with message (if any)
    return render_template('forgot.html', msg=msg) 

@app.route('/setpswd', methods=['GET', 'POST'])
def setpswd():
    msg=''
    if request.method == 'POST' and 'pswd' in request.form and 'con_pswd' in request.form:
        pswd= request.form['pswd']
        con_pswd= request.form['con_pswd'] 
        if pswd==con_pswd:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE register SET pswd=%s WHERE phone= %s', (pswd,mobile ,))
            cursor.execute('UPDATE register SET con_pswd=%s WHERE phone= %s', (con_pswd,mobile,))
            mysql.connection.commit() 
            return redirect(url_for('login'))
        else:
            msg='Password did not Match' 

    return render_template('reset.html', msg=msg) 

@app.route('/crop', methods=['GET', 'POST'])
def crop():
    return render_template('crop.html') 

@app.route('/rainfall', methods =['POST','GET'])
def rainfall(): 
    
    msg='' 
    list=[]
    if request.method == 'POST' and 'month' in request.form and 'location' in request.form and 'year' in request.form:
        month =request.form["month"]
        location= request.form["location"]
        year= request.form["year"]
        if len(str(year))==4: 
            t=[[location,int(year),month]]
            payload_scoring = {"input_data":  [{"fields": [["l","y","m"]], "values":t}]}
            response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/c55037c7-0ca7-4482-bbe3-d2c6aaec0811/predictions?version=2022-11-18', json=payload_scoring, 
                                             headers={'Authorization': 'Bearer ' + mltoken}) 
            print("Scoring response") 
            print(response_scoring.json())
            pred= response_scoring.json()
            output=pred['predictions'][0]['values'][0][0] 
            print(output) 
            res=float("{:.2f}".format(output))  
            out=str(res)+"cm"
            if res>=0 and res<=15:
                list=["Sponge gourd","Bottle Gourd","Coriander","Daisy","Carrot"]
            elif res>=16 and res<=50:
                list=["Cotton", "Sugarcane","Barley","Cucumber", "Pumpkin", "Bitter gourd", "Chili", "Beans", "Cauliflower", "Cluster beans", "Soyabean", "Green amarnath", "Kasturi methi", "Tinda" ,"Custard apple", "Watermelon", "Rose", "Sunflower", "Lilly"]
            elif res>51 and res<=75:
                list=["Wheat", "Millet", "Ragi", "Maize", "Cotton", "Sugarcane", "Groundnuts", "Barley", "Mustard", "Brinjal", "Onion" , "Capsicum", "Spring Onion", "Beetroot" , "Spinach", "Fenugreek", "Garlic", "Soyabean", "Mushroom", "Broad beans", "Green amaranth", "Kasturi methi", "Mango", "Custard apple", "Watermelon", "Sunflower", "Brama kamal", "Iris"]
            elif res>76 and res<=100:
                list=["Wheat", "Millets", "Ragi", "Maize", "Cotton", "Sugarcane", "Groundnuts", "Barley", "Mustard", "Tomato", "Brinjal", "Onion", "Capsicum", "Ladies finger","Spring Onion", "Beetroot", "Spinach", "Fenugreek","Garlic", "Soyabean", "Broccoli", "Broad beans", "Green amarnath", "Mango", "Apple", "Pine apple", "Custard apple", "Lotus", "Jasmin"] 
            elif res>101 and res<=150:
                list=["Ragi", "Sugarcane", "Capsicum", "Beetroot", "Spinach", "Ridge gourd", "Chayote", "Pointed gourd","Drumstick", "Spine gourd", "Green amarnath", "Turnip", "Mango", "Apple", "Pine apple", "Lotus"] 
            elif res>151 and res<=200:
                list=["Rice", "Chayote", "Spine gourd", "Green amarnath", "Turnip", "Mango", "Banana", "Pine apple", "Lotus", "Jute"] 
            elif res>201 and res<=250:
                list=["Rice" , "Spine gourd", "Green amarnath", "Turnip", "Mango", "Banana", "Pine apple"]
            elif res>251 and res<=300:
                list=["Rice", "Ginger","Green amarnath","Turnip","Mango","Banana","Orchid"]
            else:
                list=["Rice","Mango"]  
            return render_template("pred.html",msg=out,list=list)
        else:
            msg="Enter Year correctly"
    return render_template('rainfall.html',msg=msg) 
 

if __name__ == '__main__' :
    app.run(debug= False)