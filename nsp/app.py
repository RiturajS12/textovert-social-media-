from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
import random
import string
from flask_mail import Mail, Message
from flask_socketio import SocketIO,join_room,leave_room
import base64
  
app = Flask(__name__)
app.secret_key=os.urandom(24)

conn=mysql.connector.connect(host="127.0.0.1",user="root",password="",database="nsp",port=3306)
cursor=conn.cursor()

app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = '2022pietcrrituraj047@poornima.org'
app.config['MAIL_PASSWORD'] = 'xTc9OWKfz5rdgJZY'

mail = Mail(app)
socketio = SocketIO(app)

def send_email(recipient, subject, body):
    msg = Message(subject, sender='2022pietcrrituraj047@poornima.org', recipients=[recipient])
    msg.body = body
    mail.send(msg)


@app.route('/')
def getStarted():
    return render_template('getstart.html')


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    name=request.form.get('uname')
    email=request.form.get('uemail')
    password =request.form.get('upassword')
    otp = ''.join(random.choices(string.digits, k=6))
    cursor.execute("""INSERT INTO `nsp_register` (`userid`, `name`, `email`, `password`, `otp`) VALUES(NULL, '{}', '{}', '{}', '{}')""".format(name, email, password, otp))
    conn.commit()
    cursor.execute("""SELECT * FROM `nsp_register` WHERE `email` LIKE '{}'""".format(email))
    subject = 'Registration OTP'
    message = f'Your OTP for registration is: {otp}'
    send_email(email, subject, message)

    return render_template('verify.html')

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    email = request.form.get('email')
    otp = request.form.get('otp')

    cursor.execute("""SELECT * FROM `nsp_register` WHERE `email` LIKE '{}' AND `otp` LIKE '{}'""".format(email,otp))
    users = cursor.fetchone()

    if len(users) > 0:
        cursor.execute("""UPDATE `nsp_register` SET `verified` = 1 WHERE `email` LIKE '{}'""".format(email))
        conn.commit()
        return render_template('signup.html')
    else:
        return render_template('verify.html')
    
@app.route('/login_validation',methods=["POST"])
def login_validation():
    email=request.form.get('email')
    password=request.form.get('password')
    cursor.execute("""SELECT * FROM `nsp_register` WHERE `email` LIKE '{}' AND `password` LIKE '{}'""".format(email,password))
    users=cursor.fetchall()
    if len(users)>0:
        session['user_id']=users[0][0]
        return render_template('index.html')
    else:
        return redirect('/sign')

@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect('/')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/sign')
def signup():
    return render_template('signup.html')

@app.route('/chat')
def chat():
    username = request.args.get('username')
    room = request.args.get('room')
    if username and room:
        return render_template('chat.html',username=username,room=room)
    else:
        return render_template('services.html')
    
@app.route('/scratch')
def scratch():
    username = request.args.get('username')
    room = request.args.get('room')
    if username and room:
        return render_template('scratch.html',username=username,room=room)
    else:
        return render_template('services.html')
    
@app.route('/chat-o-vert')
def chatovert():
    return render_template('chat-o-vert.html')

@app.route('/scratchvert')
def scratchovert():
    return render_template('scratchvert.html')
    
@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],data['room'],data['message']))
    socketio.emit('receive_message', data, room=data['room'])

@socketio.on('send_image')
def handle_send_image_event(data):
    image_file = data.get('image')
    if image_file:
        try:
            with open(image_file, 'rb') as file:
                image_data = base64.b64encode(file.read()).decode('utf-8')
                data['image'] = image_data
        except Exception as e:
            print(f"Error: {e}")


    app.logger.info("{} has sent an image to the room {}".format(data['username'], data['room']))
    socketio.emit('receive_image', data, room=data['room'])

@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])


if __name__=="__main__":
   socketio.run(app,debug=True)