import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

from pymongo import MongoClient
client = MongoClient('mongodb+srv://test:sparta@cluster0.aphlzi8.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.miniPJ

@app.route('/')
# 메인 페이지 렌더
def home():
    # 로그인 성공후, 쿠키에 저장한 값을 가져온다.
    token_receive = request.cookies.get('mytoken')
    try:
        # 암호화를 푼다 (토큰+시크릿키+알고리즘) / user정보를 찾는다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        user = user_info['username']
        return render_template('index.html', user = user )
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
# 로그인 페이지 렌더
def login():
    # msg = request.args.get("msg")
    return render_template('login.html')


@app.route('/sign_in', methods=['POST'])
# 로그인
def sign_in():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    print('로그인 유저 정보', username_receive)

    # 회원가입 때와 같은 방법으로 pw를 암호화한다. 암호화한 pw값으로 매칭되는 유저를 찾는다
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=5)  # 로그인 24시간 유지
            # 'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        # localhost:5000에서는 .decode('utf-8')삭제후 실행, 배포시 .decode('utf-8')를 포함
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        print('db저장 완료 :', payload['id'])
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/check_dup', methods=['POST'])
# ID 중복확인
def check_dup():
    username_receive = request.form['username_give']

    # id중복확인의 결과를 T(중복있음),F(없음)로 exists에 저장함
    exists = bool(db.users.find_one({"username": username_receive}))
    print(exists,'중복없음-사용가능')
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_up/save', methods=['POST'])
# 회원가입
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }
    print(doc)
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)