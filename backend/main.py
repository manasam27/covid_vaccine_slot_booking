from enum import unique
from flask import Flask, json,redirect,render_template,flash,request
from flask.globals import request,session
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm.session import Session
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_required,logout_user,login_user,login_manager,LoginManager,current_user
from flask_mail  import Mail
import json
import os


#mydatabase connection

local_server=True
app=Flask(__name__)
app.secret_key="hkmm"

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, 'config.json'), 'r') as c:
    params=json.load(c)["params"]

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail=Mail(app) 

login_manager=LoginManager(app)
login_manager.login_view='login'

# app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:password@localhost/databasename' 
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/covid' 
db=SQLAlchemy(app)

   
# Callback for login management, will be called on whenever login session is to be checked
# or restored.
# TODO: Manage hospital user seperately.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))
    


class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    aadharno=db.Column(db.String(20))
    email=db.Column(db.String(50))
    dob=db.Column(db.String(1000))

class Hospitaluser(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    email=db.Column(db.String(50))
    password=db.Column(db.String(1000))

class Hospitaldata(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20),unique=True)
    hname=db.Column(db.String(100))
    vvaxin=db.Column(db.Integer)    
    vshield=db.Column(db.Integer)
    vsputnik=db.Column(db.Integer)

class Booking(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    aadharno=db.Column(db.String(20),unique=True)
    vaccinetype=db.Column(db.String(20))
    hcode=db.Column(db.String(20))
    pname=db.Column(db.String(20))
    gender=db.Column(db.String(10)) 
    pphone=db.Column(db.String(12))    
    paddress=db.Column(db.String(50))
    age=db.Column(db.Integer)  

class Trig(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    hcode=db.Column(db.String(20))
    vvaxin=db.Column(db.Integer)    
    vshield=db.Column(db.Integer)
    vsputnik=db.Column(db.Integer)
    querys=db.Column(db.String(20))
    date=db.Column(db.String(20))



@app.route("/")
def home():
    return render_template("index.html")  

@app.route("/trigers")
def trigers():
    query=Trig.query.all()
    return render_template("trigers.html",query=query)       

@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method=="POST":
        aadharno=request.form.get('aad')
        email=request.form.get('email')
        dob=request.form.get('dob')
        # print(aadharno,email,dob) 
        encpassword=generate_password_hash(dob)
        user=User.query.filter_by(aadharno=aadharno).first()
        emailUser=User.query.filter_by(email=email).first()
        if user or emailUser:
            flash("Email or aadharno is already taken","warning")
            return render_template("usersignup.html")
        new_user=db.engine.execute(f"INSERT INTO `user` (`aadharno`,`email`,`dob`) VALUES ('{aadharno}','{email}','{encpassword}')")
        
        flash("SignIn Success","success")
        return render_template("userlogin.html")

    return render_template("usersignup.html")


@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":
        aadharno=request.form.get('aad')
        dob=request.form.get('dob')
        user=User.query.filter_by(aadharno=aadharno).first()
    

        if user and check_password_hash(user.dob,dob):
            login_user(user)
            flash("Login success","info")
            return render_template("index.html")
        else:
            flash("Invalid credentials","danger")
            return render_template("userlogin.html")   


    return render_template("userlogin.html")


@app.route('/hospitallogin',methods=['POST','GET'])
def hospitallogin():
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=Hospitaluser.query.filter_by(email=email).first()
    

        if user and check_password_hash(user.password,password):
            ok = login_user(user)
            if ok:
                # POST valid
                flash("Login success","info")
                return render_template("index.html")
        # POST invalid
        flash("Invalid credentials","danger")
        return render_template("hospitallogin.html")   
    # GET
    return render_template("hospitallogin.html")



@app.route('/admin',methods=['POST','GET'])
def admin():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        if(username==params['user'] and password==params['password']):
            session['user']=username
            flash("Login Success","info")
            return render_template("addHosUser.html")  
        else:
            flash("Invalid Credentials","danger")     

    return render_template("admin.html")  

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))


@app.route('/addHospitalUser',methods=['POST','GET'])
def hospitalUser():

    if('user' in session and session['user']==params['user']):
        if request.method=="POST":
            hcode=request.form.get('hcode')
            email=request.form.get('email')
            password=request.form.get('password')
            encpassword=generate_password_hash(password)
            hcode=hcode.upper()
            emailUser=Hospitaluser.query.filter_by(email=email).first()
            if emailUser:
                flash("Email already exists","warning")
            db.engine.execute(f"INSERT INTO `hospitaluser` (`hcode`,`email`,`password`) VALUES ('{hcode}','{email}','{encpassword}')")
           
            mail.send_message('COVID CARE CENTER', sender=params['gmail-user'],recipients=[email],body=f"Welcome!!\nThanks for choosing us.\nYour login credentials are:\nEmail Address: {email}\nPassword: {password}\nHospital code: {hcode}\n\n\nDo not share your password with anyone.\n\n\nThank you...:)")
           
            flash("Data sent and Inserted successfully","success")
            return render_template("addHosUser.html")
    else:
        flash("Login and try again","warning")
        return render_template("addHosUser.html")




#test db connected or not
@app.route("/test")
def test():
    em=current_user.email
    print(em) 
    try:
        a=Test.query.all()
        print(a)
        return 'MY DATABASE IS CONNECTED'
    except Exception as e:
        print(e)
        return 'MY DATABASE IS NOT CONNECTED'     

@app.route('/logoutadmin')
def logoutadmin():
    session.pop('user')
    flash("Admin logout successful","primary")
    return redirect('/admin')          

@app.route('/addhospitalinfo',methods=['POST','GET'])
def addhospitalinfo():
    # load_user()
    email=current_user.email
    posts=Hospitaluser.query.filter_by(email=email).first()
    code=posts.hcode
    postsdata=Hospitaldata.query.filter_by(hcode=code).first()
    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        vvaxin=request.form.get('vvaxin')
        vshield=request.form.get('vshield')
        vsputnik=request.form.get('vsputnik')
        hcode=hcode.upper()
        huser=Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser=Hospitaldata.query.filter_by(hcode=hcode).first() #to not let the same hospital add data again
        if hduser:
            flash("Data is already present you can update it.","primary")
            return render_template("hospitaldata.html")
        if huser:
            db.engine.execute(f"INSERT INTO `hospitaldata` (`hcode`,`hname`,`vvaxin`,`vshield`,`vsputnik`) VALUES ('{hcode}','{hname}','{vvaxin}','{vshield}','{vsputnik}')")
            flash("Data Added","info")
        else:
            flash("Hospital code doesn't exist","warning")    

    return render_template("hospitaldata.html",postsdata=postsdata)


@app.route("/hedit/<string:id>",methods=['POST','GET'])
@login_required
def hedit(id):
    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        vvaxin=request.form.get('vvaxin')
        vshield=request.form.get('vshield')
        vsputnik=request.form.get('vsputnik')
        hcode=hcode.upper()
        db.engine.execute(f"UPDATE `hospitaldata` SET `hcode`='{hcode}',`hname`='{hname}',`vvaxin`='{vvaxin}',`vshield`='{vshield}',`vsputnik`='{vsputnik}' WHERE `hospitaldata`.`id`={id}")
        flash("Slot updated","info")
        return redirect("/addhospitalinfo") 

    posts=Hospitaldata.query.filter_by(id=id).first()
    return render_template("hedit.html",posts=posts)



@app.route("/hdelete/<string:id>",methods=['POST','GET'])
@login_required
def hdelete(id):
    db.engine.execute(f"DELETE FROM `hospitaldata` WHERE `hospitaldata`.`id`={id}")
    flash("Data deleted","danger")
    return redirect("/addhospitalinfo") 

@app.route("/pdetails",methods=['GET'])
@login_required
def pdetails():
    code=current_user.aadharno
    print(code)
    data=Booking.query.filter_by(aadharno=code).first()
    print(data)
    return render_template("details.html",data=data)     


@app.route("/slotbooking",methods=['POST','GET'])
@login_required
def slotbooking():
    query=db.engine.execute(f"SELECT * FROM `hospitaldata`")
    if request.method=="POST":
        aadharno=request.form.get('aadharno')
        vaccinetype=request.form.get('vaccinetype')
        hcode=request.form.get('hcode')
        pname=request.form.get('pname')
        gender=request.form.get('gender')
        pphone=request.form.get('pphone')
        paddress=request.form.get('paddress')
        age=request.form.get('age')
        check2=Hospitaldata.query.filter_by(hcode=hcode).first()
        if not check2:
            flash("Hospital code does not exist","warning")
        code=hcode
        dbb=db.engine.execute(f"SELECT * FROM `hospitaldata` WHERE `hospitaldata`.`hcode`='{code}'")
        vaccinetype=vaccinetype
        if vaccinetype=="covaxin":
            for d in dbb:
                seat=d.vvaxin
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=hcode).first()
                ar.vvaxin=seat-1
                db.session.commit()

        elif vaccinetype=="covishield":
            for d in dbb:
                seat=d.vshield
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=hcode).first()
                ar.vshield=seat-1
                db.session.commit()

        elif vaccinetype=="sputnik":
            for d in dbb:
                seat=d.vsputnik
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=hcode).first()
                ar.vsputnik=seat-1
                db.session.commit()  

        else:
            pass
        check=Hospitaldata.query.filter_by(hcode=hcode).first()  
        if(seat>0 and check):
            res=Booking(aadharno=aadharno,vaccinetype=vaccinetype,hcode=hcode,pname=pname,gender=gender,pphone=pphone,paddress=paddress,age=age)
            db.session.add(res)
            db.session.commit()
            flash("Slot is booked. Kindly visit the hospital for further procedure","success")
        else:
            flash("Something went wrong","danger")    


    return render_template("booking.html",query=query)   


app.run(debug=True)