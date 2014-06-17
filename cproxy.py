import socket, sys, os, asyncore, time
from urlparse import urlparse

BackLog = 50
Max_Data = 999999

class Proxy_Server(asyncore.dispatcher):
	def __init__(self, address):
		asyncore.dispatcher.__init__(self)
		try:
			self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
			self.bind(address)
			self.listen(BackLog)
		except socket.error, (value, message):
			if self:
				self.close()
			print "Could not open socket: ", message
			sys.exit(1)

	def handle_accept(self):
		conn, client_addr = self.accept()
		Proxy_Send_Recv_Cli_Handler(conn, client_addr)
		
	def handle_close(self):
		print "Proxy_Server: handle_close"
		self.close()

class Proxy_Send_Recv_Cli_Handler(asyncore.dispatcher):
	def __init__(self, conn, client_addr):
		asyncore.dispatcher.__init__(self, sock=conn)
		self.conn = conn 

	def handle_read(self):
		request = self.recv(1024)
		if request:
			first_line = request.split('\n')[0]
			url = urlparse(first_line.split(' ')[1])
			host = url.hostname
			port = 80
			Proxy_Get_Header_Handler(host, port, request, self.conn)

	def handle_close(self):
		print "Client close"
		self.close()

class Proxy_Get_Header_Handler(asyncore.dispatcher):
	def __init__(self, host, port, request, conn):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect((host, port))
		self.request = request
		self.host = host
		self.port = port
		self.conn = conn

	def handle_connect(self):
		head_request = self.request.replace("GET", "HEAD")
		self.send(head_request)

	def handle_read(self):
		data = self.recv(3000)
		content_len = data[data.index("Content-Length: ")+16:]
		content_len = content_len[:content_len.index("\r\n")]
		if int(content_len) < 10000:
			Proxy_Send_Recv_Ser_Handler(self.host, self.port, self.request, self.conn)
			self.close()
		else:
			Proxy_Accelerator(self.host, self.port, self.request, self.conn, content_len)
			self.close()

	def handle_close(self):
		print "Header Close!!"
		self.close()

class Proxy_Send_Recv_Ser_Handler(asyncore.dispatcher):
	def __init__(self, host, port, request, conn):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect((host, port))
		self.request = request
		self.conn = conn 

	def handle_connect(self):
		self.send(self.request)

	def handle_read(self):
		data = self.recv(1024)
		if len(data) > 0:
			self.conn.send(data)
		else:
			self.close()

	def handle_close(self):
		print "Server close"
		self.close()

class Proxy_Accelerator(asyncore.dispatcher):
	def __init__(self, host, port, request, conn, content_len):
		asyncore.dispatcher.__init__(self)
		self.request = request
		self.conn = conn 
		self.content_len = content_len
		self.host = host
		self.port = port
		start = 0
		end = 10000
		while True:
			if start+10000 < int(self.content_len):
				acc_request = self.request[:self.request.index("\r\n\r\n")] + "\r\nRange: bytes=%i-%i\r\n\r\n" %(start, end)
				Proxy_Accelerator_Handler(self.host, self.port, acc_request, self.conn)
				start += 10000
				end += 10000
			else:
				acc_request = self.request[:self.request.index("\r\n\r\n")] + "\r\nRange: bytes=%i-\r\n\r\n" %(start)
				Proxy_Accelerator_Handler(self.host, self.port, acc_request, self.conn)
				break

	def handle_close(self):
		print ("Accelerator Close!!!")
		self.close()

class Proxy_Accelerator_Handler(asyncore.dispatcher):
	def __init__(self, host, port, request, conn):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect((host, port))
		self.request = request
		self.conn = conn 

	def handle_connect(self):
		print self.request
		self.send(self.request)

	def handle_read(self):
		data = self.recv(1024)
		print data
		if len(data) > 0:
			self.conn.send(data)
		else:
			self.close()

	def handle_close(self):
		print "Proxy_Accelerator Close!!!!"
		self.close()

if __name__ == '__main__':
	Proxy_Server(('', 8080))
	asyncore.loop()