import socketserver, time
import pickle
import threading
myHost = ''
myPort = 50007


def now():
    return time.ctime(time.time())

def send_com(conn):
    #reply = pickle.dumps(['add', '/home/midway/test/th'])
    while True:
        reply = pickle.dumps([x for x in input().strip().split()])
        conn.send(reply)
        data = conn.recv(1024)
        if not data:
            time.sleep(1)
            continue
        print(pickle.loads(data))
        #time.sleep(36)

class MyClienthandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        print(self.client_address, now())
        #time.sleep(5)
        #self.request.send('WELCOME STRING'.encode())
        x = threading.Thread(target=send_com, args=(self.request, ))
        x.start()

        while True:
            data = self.request.recv(1024)
            if not data:
                time.sleep(1)
                continue
            reply = pickle.dumps(['OK', now()])
            self.request.send(reply)
            ans = pickle.loads(data)
            #if ans
            print(pickle.loads(data))
            #reply = pickle.dumps(['add', '/home/midway/config.txt'])
            #self.request.send(reply)
        #self.request.close()
        #print('close connection')


myaddr = (myHost, myPort)
server = socketserver.ThreadingTCPServer(myaddr, MyClienthandler)
server.serve_forever()