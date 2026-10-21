# Curriculum setup - run these in powershell
1.dowload from github
git clone https://github.com/xam673/Curriculum

2.set dir, env and install
cd curriculum-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirement.txt

3.create demo data
python seed.py

4.run local server
uvicorn app.main:app --reload

5.open interactive demo
# open this link on browser - http://127.0.0.1:8000/docs

Testing
GET /auth/mock-users → "Try it out" → Execute. You should see 4 users.

POST /auth/mock-login with {"user_id": 3} (a student). Copy the access_token from the response.

Click Authorize (top right), paste the token, and confirm.

GET /courses with q=calc. You should get Calculus I and II.

GET /courses with category=Major Elective.

POST /admin/courses as the student. You should get 403, which shows its working.

Log in as user_id: 1 (admin), authorize with the new token, and try the POST again. It should succeed.

Try creating a course with "code": "abc" or "credits": -1. You should get 422, which shows its working.