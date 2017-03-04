import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1',8888))
print s.recv(1024)
s.send("hello2")
