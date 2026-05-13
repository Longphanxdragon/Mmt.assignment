# Tai lieu demo chi tiet - AsynapRous (CO3094)

Muc tieu tai lieu
- Ban co the demo truoc lop trong 3-7 phut.
- Ban biet chinh xac phai go lenh gi trong terminal.
- Ban biet doc output de chung minh bai da chay dung.
- Ban co script noi san de tu tin trinh bay.
- Ban hieu ly thuyet cot loi: non-blocking HTTP, proxy, route, request/response, log, packet.

--------------------------------------------------
PHAN 1 - CHUAN BI TRUOC KHI DEMO
--------------------------------------------------

1) Mo dung thu muc du an
- Lenh:
  cd /workspaces/Mmt.assignment

- Ky vong:
  Khong bao loi. Neu go lenh pwd thi thay duong dan ket thuc bang /workspaces/Mmt.assignment.

2) Bao dam script co quyen chay
- Lenh:
  chmod +x run-dev.sh stop-dev.sh

- Ky vong:
  Thuong khong in gi. Neu co loi permission denied thi chay lai lenh tren.

3) Dam bao khong con tien trinh cu
- Lenh:
  ./stop-dev.sh

- Cach doc output:
  - Neu dang co tien trinh, ban se thay dong Killing PID ...
  - Neu khong co gi de tat, script van ket thuc binh thuong.

--------------------------------------------------
PHAN 2 - KICH BAN DEMO NHANH (3 PHUT)
--------------------------------------------------

Buoc A - Bat he thong
- Lenh:
  ./run-dev.sh

- Cach doc output de chung minh:
  - Co dong Starting sampleapp on port 9001...
  - Co dong Starting proxy on port 8080...
  - Co dong Services started...

- Y nghia:
  - sampleapp la backend app.
  - proxy la cua vao ben ngoai de nhan request.

Buoc B - Test API GET
- Lenh:
  curl -i http://127.0.0.1:8080/get-list -H "Host: localhost:8080"

- Cach doc output:
  1. Dong trang thai: HTTP/1.1 200 OK
  2. Header: Content-Type: application/json
  3. Body (nam duoi dong trong): {"active_peers": []}

- Cach noi voi lop:
  "Em gui GET qua cong 8080 (proxy). Server tra ve 200 OK va body JSON hop le."

Buoc C - Test API POST
- Lenh:
  curl -i -X POST http://127.0.0.1:8080/echo -H "Host: localhost:8080" -H "Content-Type: application/json" -d '{"text":"demo"}'

- Cach doc output:
  1. HTTP/1.1 200 OK
  2. Body JSON chua lai gia tri vua gui, vi du: {"received": {"text": "demo"}}

- Cach noi voi lop:
  "Endpoint echo tra lai dung payload em gui, chung minh route POST va parse JSON da hoat dong."

Buoc D - Demo xac thuc (authorized)
- Lenh 1 - gui sai thong tin de xem 401:
  curl -i -X POST http://127.0.0.1:9001/login -H "Content-Type: application/json" -d '{"text":"abc"}'

- Cach doc output:
  - HTTP/1.1 401 ERROR
  - Header co WWW-Authenticate: Basic realm="AsynapRous"
  - Body: {"error": "unauthorized"}

- Cach noi voi lop:
  "Day la phan unauthorized. Khi khong co thong tin xac thuc dung, server tu choi login."

- Lenh 2 - dang nhap thanh cong bang Basic Auth:
  curl -i -X POST http://127.0.0.1:9001/login -u student:pass123

- Cach doc output:
  - HTTP/1.1 200 OK
  - Header co Set-Cookie: sessionid=...
  - Body: {"message": "login ok", "session": "..."}

- Cach noi voi lop:
  "Day la phan authorized. Em gui dung username/password, server tra ve session cookie de dung cho lan sau."

- Lenh 3 - kiem tra session bang whoami:
  curl -i http://127.0.0.1:9001/whoami -H "Cookie: sessionid=<copy_sessionid_from_login>"

- Cach doc output:
  - HTTP/1.1 200 OK
  - Body: {"authenticated": true, "user": "student"}

- Cach noi voi lop:
  "Sau khi login thanh cong, em dung cookie sessionid de chung minh server nhan ra user da xac thuc."

Buoc D - Tat he thong
- Lenh:
  ./stop-dev.sh

- Cach doc output:
  - Co dong Killing PID ...
  - Co dong Stopped dev services...

- Cach noi voi lop:
  "He thong duoc quan ly bang PID file, tat sach tien trinh sau demo."

--------------------------------------------------
PHAN 3 - KICH BAN DEMO DAY DU (5-7 PHUT)
--------------------------------------------------

1) Chay lai tu dau
  ./stop-dev.sh
  ./run-dev.sh

2) Chung minh cong dang lang nghe
  ss -ltnp | grep -E ':8080|:9001'

- Cach doc output:
  - Thay 2 dong LISTEN cho 8080 va 9001.

3) Test 4 route chinh
  echo '1) GET /get-list'
  curl -sS -i --max-time 10 http://127.0.0.1:8080/get-list -H 'Host: localhost:8080'
  echo
  echo '2) POST /echo'
  curl -sS -i --max-time 10 -X POST http://127.0.0.1:8080/echo -H 'Host: localhost:8080' -H 'Content-Type: application/json' -d '{"text":"demo cho lop"}'
  echo
  echo '3) POST /login (khong auth)'
  curl -sS -i --max-time 10 -X POST http://127.0.0.1:8080/login -H 'Host: localhost:8080' -H 'Content-Type: application/json' -d '{"text":"abc"}'
  echo
  echo '4) PUT /hello'
  curl -sS -i --max-time 10 -X PUT http://127.0.0.1:8080/hello -H 'Host: localhost:8080' -H 'Content-Type: application/json' -d '{"text":"hi"}'

- Cach doc output chuan:
  - GET /get-list: 200 OK + JSON danh sach peer.
  - POST /echo: 200 OK + JSON phan hoi dung noi dung gui.
  - POST /login: 401 ERROR neu chua co auth (day la hanh vi mong doi).
  - PUT /hello: hien tai co the tra ve chuoi coroutine object (chi ra bug async chua await).

4) Chung minh bang log server
  tail -n 40 logs/sampleapp.log
  tail -n 20 logs/proxy.log

- Cach doc output:
  - Tim dong Request ... GET /get-list
  - Tim dong Request ... POST /echo
  - Tim canh bao RuntimeWarning: coroutine ... was never awaited (neu co)

5) Ket thuc demo
  ./stop-dev.sh

--------------------------------------------------
PHAN 4 - SCRIPT NOI SAN TRUOC LOP (BAN DOC THEO)
--------------------------------------------------

Mo dau (20-30 giay)
"Nhom em xay dung he thong HTTP non-blocking gom 2 thanh phan: proxy nghe cong 8080 va sample backend nghe cong 9001. Em se demo theo luong bat he thong, gui request, doc response, va doi chieu log."

Phan chay he thong (20 giay)
"Em chay run-dev.sh de khoi dong dong thoi proxy va backend. Output hien ro 2 cong dang duoc khoi dong."

Phan GET (30 giay)
"Em gui GET /get-list qua proxy. Ket qua 200 OK va body JSON active_peers. Dieu nay xac nhan request qua proxy vao backend va tra ve dung dinh dang."

Phan POST (40 giay)
"Em gui POST /echo kem JSON text demo. Server tra lai chinh payload da gui. Chung minh route POST va parse JSON hoat dong dung."

Phan auth (30 giay)
"Em gui POST /login khong kem thong tin xac thuc. Server tra 401 Unauthorized, cho thay co co che auth can ban."

Phan log va dong he thong (30-40 giay)
"Em mo log sampleapp de thay vet xu ly request. Cuoi cung em stop-dev.sh de kill tien trinh theo PID file, tranh process treo."

Neu giang vien hoi ve loi PUT /hello
"Hien tai route nay co dau hieu coroutine chua duoc await, nhom da nhan dien duoc trong log RuntimeWarning va se fix phan async handler de tra JSON dung thay vi coroutine object."

--------------------------------------------------
PHAN 5 - CACH DOC OUTPUT (QUAN TRONG NHAT)
--------------------------------------------------

Khi dung curl -i
- Phan 1: Status line
  Vi du: HTTP/1.1 200 OK

- Phan 2: Header
  Vi du: Content-Type, Content-Length, WWW-Authenticate...

- Phan 3: Body
  Nam sau 1 dong trong.
  Vi du:
  {"active_peers": []}
  hoac
  {"received": {"text": "demo"}}

Neu ban muon nhin body cho de
- Dung lenh khong co -i:
  curl -sS -X POST http://127.0.0.1:8080/echo -H "Host: localhost:8080" -H "Content-Type: application/json" -d '{"text":"demo"}'

- Luc nay terminal chi in body JSON.

--------------------------------------------------
PHAN 6 - LY THUYET LIEN QUAN (DE HIEU TAT TAN TAT)
--------------------------------------------------

1) HTTP request/response
- Request gom: Method + Path + Header + Body.
- Response gom: Status line + Header + Body.
- 200 la thanh cong.
- 401 la chua du quyen (can auth).

2) Proxy la gi
- Client gui vao proxy (8080).
- Proxy dinh tuyen request den backend phu hop (9001).
- Loi ich: tach lop, de scale, de route theo host/path.

3) Non-blocking la gi
- Blocking: dang cho I/O thi luong bi dung, khong lam viec khac.
- Non-blocking: khi cho I/O, event loop chuyen sang xu ly ket noi khac.
- Loi ich: phuc vu nhieu ket noi dong thoi, dung tai nguyen tot hon.

4) Coroutine va canh bao never awaited
- Ham async tra ve coroutine object.
- Neu khong await coroutine do, Python canh bao never awaited.
- Hau qua: logic async co the khong duoc thuc thi dung.

5) Tai sao can log
- Log la bang chung server da nhan request.
- Log giup truy vet duong di va debug loi runtime.

6) PID file trong script start/stop
- run-dev.sh luu PID cua process.
- stop-dev.sh doc PID va kill process do.
- Giup tat dung tien trinh, khong tat nham.

--------------------------------------------------
PHAN 7 - FAQ NHANH (GIANG VIEN HAY HOI)
--------------------------------------------------

Hoi: Neu khong co giao dien dep thi co sao khong?
Tra loi: Khong sao. Bai nay trong tam la network/backend non-blocking. UI chi la cong cu gui request.

Hoi: Lam sao chung minh request di qua he thong?
Tra loi: Chung minh bang 3 tang: output curl, cong LISTEN, va log sampleapp/proxy.

Hoi: Tai sao login 401?
Tra loi: Do endpoint yeu cau xac thuc, gui request khong co auth se bi tu choi theo dung nguyen tac HTTP.

Hoi: Neu thieu thoi gian demo?
Tra loi: Chay kich ban 3 phut (run-dev -> GET -> POST echo -> stop-dev).

--------------------------------------------------
PHAN 8 - CHEAT SHEET 30 GIAY TRUOC KHI LEN BANG
--------------------------------------------------

Lenh toi gian:
  cd /workspaces/Mmt.assignment
  ./run-dev.sh
  curl -i http://127.0.0.1:8080/get-list -H "Host: localhost:8080"
  curl -i -X POST http://127.0.0.1:8080/echo -H "Host: localhost:8080" -H "Content-Type: application/json" -d '{"text":"demo"}'
  ./stop-dev.sh

Thong diep toi gian:
- Da start duoc proxy va backend.
- GET va POST tra 200 + JSON hop le.
- Da stop sach process theo PID.

Ket luan
- Demo dat yeu cau cot loi cua bai: chay he thong, route request, tra response, co quan sat log, va quan ly tien trinh.

--------------------------------------------------
PHAN 9 - DEMO CHAT WEB APP P2P (BAT BUOC)
--------------------------------------------------

Muc tieu
- Hien login/auth that tren tung peer server.
- Lay danh sach peer online tu tracker.
- Gui tin truc tiep giua cac peer bang HTTP /send-peer va /receive-message.
- Demo duoc moi lien he giua browser UI, authorized session, va non-blocking backend.

Buoc 1 - Mo giao dien chat
- Chay server tinh cho `chat.html`:
  cd /workspaces/Mmt.assignment
  python3 -m http.server 8001

- Mo browser:
  http://127.0.0.1:8001/chat.html?name=alice

Buoc 2 - Chay tracker va 4 peer server rieng
```bash
python3 CO3094-asynaprous/start_sampleapp.py --server-port 9001
python3 CO3094-asynaprous/start_sampleapp.py --server-port 9002
python3 CO3094-asynaprous/start_sampleapp.py --server-port 9003
python3 CO3094-asynaprous/start_sampleapp.py --server-port 9004
python3 CO3094-asynaprous/start_sampleapp.py --server-port 9005
```

Buoc 3 - Mo 4 tab browser khac nhau
- Trang 1: `http://127.0.0.1:8001/chat.html?name=alice&peerport=9002&tracker=localhost:9001`
- Trang 2: `http://127.0.0.1:8001/chat.html?name=bob&peerport=9003&tracker=localhost:9001`
- Trang 3: `http://127.0.0.1:8001/chat.html?name=charlie&peerport=9004&tracker=localhost:9001`
- Trang 4: `http://127.0.0.1:8001/chat.html?name=dave&peerport=9005&tracker=localhost:9001`

Buoc 4 - Dang nhap va dang ky tracker
- Moi tab nhap `student / pass123` roi bam `Login + Register`.
- Quan sat dong trang thai cho biet login thanh cong va co session user.
- Bam `Lam moi danh sach` de lay danh sach peer online tu tracker.
- Phai thay cac peer con lai trong danh sach ben trai.

Buoc 5 - Chat truc tiep qua backend
- Trang alice chon bob, nhap `Xin chao Bob`, bam `Gui`.
- Trang bob se nhan message qua backend trong khung chat.
- Trang charlie chon alice hoac dave de chat thu tiep.
- Trang dave reply lai va cac trang con lai se thay message khi poll lai backend.

Buoc 6 - Kiem tra auth bang curl neu giang vien hoi
- Lenh:
```bash
curl -i -X POST http://127.0.0.1:9002/login -u student:pass123
curl -i http://127.0.0.1:9002/whoami -H "Cookie: sessionid=<sessionid>"
```

- Khi login dung, server tra `200 OK` va `Set-Cookie: sessionid=...`.
- Khi goi `whoami`, server tra `authenticated: true` neu cookie hop le.

Buoc 7 - Tat he thong
- Dong terminal chay `python3 -m http.server 8001` va cac peer server.
- Nen stop tung server de tranh process treo.

Script noi san
- "Phan demo chat khong con la broadcast trong browser. Em dung mot tracker de luu danh sach peer online, moi peer co mot server rieng, browser UI login vao tung peer server bang session cookie, sau do lay peer list va gui tin qua /send-peer. Khi em nhan Login + Register va chat giua 4 trang, do la dang chay backend HTTP that, vua co auth vua co trao doi P2P giua cac tien trinh."

--------------------------------------------------
PHAN 10 - KET QUA THUC TE (SMOKE TESTS)
--------------------------------------------------

Duoi day la cac lenh va ket qua minh da chay tren moi server (tat ca tren localhost). Ban co the copy/paste cac lenh nay khi demo.

1) Login (curl) - sample
```
HTTP/1.1 200 OK
Set-Cookie: sessionid=fe3797d7...; Path=/; HttpOnly
{"message": "login ok", "session": "fe3797d7..."}
```

2) Whoami - sample
```
HTTP/1.1 200 OK
{"authenticated": true, "session": "fe3797d7...", "user": "student"}
```

3) Tracker list after registering peers
```
{
  "active_peers": [
    {"peer_id":"alice","ip":"127.0.0.1","port":9002},
    {"peer_id":"bob","ip":"127.0.0.1","port":9003},
    {"peer_id":"charlie","ip":"127.0.0.1","port":9004},
    {"peer_id":"dave","ip":"127.0.0.1","port":9005}
  ]
}
```

4) Direct send (alice -> bob)
```
{"status":"message_sent","target":"bob","message":{"sender":"alice","target_peer_id":"bob","content":"Xin chao Bob","type":"direct","timestamp":1}}
```

5) Bob's messages after receive
```
{
  "messages": [
    {"sender":"alice","target_peer_id":"bob","content":"hello bob after await fix","type":"direct","timestamp":0},
    {"sender":"alice","target_peer_id":"bob","content":"Xin chao Bob","type":"direct","timestamp":1}
  ],
  "total": 2
}
```

Ghi chu: cac ket qua tren cho thay cac endpoint chinh hoat dong: `/login`, `/whoami`, `/submit-info`, `/get-list`, `/send-peer`, va `/get-messages`.
