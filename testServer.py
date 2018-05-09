#!/usr/bin/env python
import subprocess, sys, os, time
from socket import * # get socket constructor and constants


class Server:
    #------------------------------------------------------------------------------------------------#
    def __init__(self):
        self.myHost    = gethostname()
        self.myPort    = 15001 
        self.addr      = (self.myHost, self.myPort)
        self.directory = 'public_html'

    #------------------------------------------------------------------------------------------------#
    def startServer(self):
        self.sockobj = socket(AF_INET, SOCK_STREAM) # make a TCP/IP socket object
        try:
            self.sockobj.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.sockobj.bind(self.addr)
            print("Server initalizaed on: %s, and port: %d") %(self.myHost, self.myPort)

        except error as err:
            print ("socket creation giving error: %s") %(err)
            sys.exit(1)

        self.waitForConnections()

    #------------------------------------------------------------------------------------------------#
    def generateHeaders(self, code, type):
        header = ''
        if  (code == 200): 
            header = 'HTTP/1.1 200 OK\n'

        elif(code == 404): 
            header = 'HTTP/1.1 404 Not Found\n'

        if (type == 'html' or type == 'cgi'):
            header += 'Content-Type: text/html\n\n'

        elif (type == 'css'):
            header += "HTTP/1.1 200 OK\nContent-Type: text/css\n\n"

        return header
    #------------------------------------------------------------------------------------------------#
    def waitForConnections(self):
        
        self.sockobj.listen(10)
        while True: 
            print ("Listening for new connection")
            responseContent = ''
            responseHeaders = ''
            connection, address = self.sockobj.accept() 

            #connection.settimeout(45)

            print('Server connected by', address[0])

            data = connection.recv(4096) 
            if not data: break

            string = bytes.decode(data) 

            requestMethod = string.split(' ')[0]

            print("METHOD IS: {m}".format(m=requestMethod))
            print("REQUEST BODY IS:\n**************************\n {b}".format(b=string))
            print("**************************")
            print("REQUEST PAGE IS:\n**************************\n {b}".format(b=string.split(' ')[1]))
            print("**************************")

#///////////////////////////////////HANDLING GET COMMANDS\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
            if requestMethod == 'GET':
                print("Serving http GET request")

                fileRequested = string.split(' ')[1]

                fileRequested = fileRequested.split('?') 

                string = ''
                if (len(fileRequested) > 1):  string = fileRequested[1]

                fileRequested = fileRequested[0]

                if(fileRequested == '/'): fileRequested = 'index.html' 

                print ("Serving web page: {b}".format(b=fileRequested))

                fileRequested = fileRequested.strip('/')

                try:
                    fileHander = open(fileRequested,'rb')
                    responseContent = fileHander.read() # read file content
                    fileHander.close()

                    if   (fileRequested.endswith(".html")):  responseHeaders = self.generateHeaders(200, 'html')
                    elif (fileRequested.endswith(".css")): responseHeaders = self.generateHeaders(200, 'css')
                    elif (fileRequested.endswith(".cgi")):
                        responseHeaders = self.generateHeaders(200, 'cgi')
                        responseContent = ''

                        if(len(string) > 1): os.environ['QUERY_STRING'] = string
                        
                        proc = subprocess.Popen(fileRequested, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                        out = proc.communicate(input = None)

                        responseContent = out[0]
                    
                        if(len(responseContent.split('Content-type: text/html\n')[0]) > 0):
                            cookie = responseContent.split('Content-type: text/html\n')[0]
                            cookie = cookie.split(':')[1]
                            os.environ['HTTP_COOKIE'] = cookie 
                        responseContent = responseContent.split('Content-type: text/html\n')[1]

                except Exception as e: #in case file was not found, generate 404 page
                    print ("Warning, file not found. Serving response code 404\n", e)
                    responseHeaders = self.generateHeaders( 404, 'html')

                    responseContent = b"""
                    <html>
                        <body>
                            <img style="display:block;" width="100%" height="100%" src="https://tincan.co.uk/sites/default/files/styles/banner_image_tincan/public/images/Blog-404-01.png?itok=G8jyKL7k" />
                        </body>
                    </html>"""

                serverResponse =  str(responseHeaders) + str(responseContent) 
                connection.send(serverResponse)
               
#///////////////////////////////////HANDLING POST COMMANDS\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
            elif requestMethod == 'POST':
                print("Serving http POST request")

                fileRequested = string.split(' ')[1]

                string = string.split('\n')
                #if there is a cookie
                if (string[-1].find('&') != -1):
                    string = string[-1]
                    part1 = string.split('&')[0]
                    part1 = part1.split('=')[1]
                    
                    part2 = string.split('&')[1]
                    part2 = part2.split('=')[1]

                    cookie = part1 + '=' + part2
                    os.environ['HTTP_COOKIE'] = cookie


                if(fileRequested == '/'): fileRequested = 'index.html' 

                print ("Serving web page: {b}".format(b=fileRequested))

                fileRequested = fileRequested.strip('/')

                try:
                    fileHander = open(fileRequested,'rb')
                    responseContent = fileHander.read() # read file content
                    fileHander.close()

                    if (fileRequested.endswith(".html")):  responseHeaders = self.generateHeaders(200, 'html')
                    elif (fileRequested.endswith(".css")): responseHeaders = self.generateHeaders(200, 'css')

                    elif (fileRequested.endswith(".cgi")):
                        responseHeaders = self.generateHeaders(200, 'cgi')

                        if (string[-1].find('&') != -1): 
                            #Sending the query string to stdin of cgi
                            out = subprocess.Popen(fileRequested, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate(input = string[-1]) 
                        else:
                            #else no query string to send
                            out = subprocess.Popen(fileRequested, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate(input = None)

                        responseContent = out[0]

                        responseContent = responseContent.split('Content-type: text/html\n')[1]
                        
                except Exception as e: #in case file was not found, generate 404 page
                    print ("Warning, file not found. Serving response code 404\n", e)
                    responseHeaders = self.generateHeaders( 404, 'html')

                    responseContent = b"""
                    <html>
                        <body>
                            <img style="display:block;" width="100%" height="100%" src="https://tincan.co.uk/sites/default/files/styles/banner_image_tincan/public/images/Blog-404-01.png?itok=G8jyKL7k" />
                        </body>
                    </html>"""

                serverResponse =  str(responseHeaders) + str(responseContent) 
                connection.send(serverResponse)

            else:
                responseHeaders = self.generateHeaders( 404, 'html')

                responseContent = b"""
                <html>
                    <body>
                        <p>unsupported HTTP method</p>
                    </body>
                </html>"""
                print("Unsupported HTTP request method:", requestMethod)                    

                serverResponse =  str(responseHeaders) + str(responseContent) 
                connection.send(serverResponse)

            connection.close()
#------------------------------------------------------------------------------------------------#
#---------------------------------End of server class--------------------------------------------#
print ("*****Starting HTTP/1.1 web server*****")
serv = Server()
serv.startServer() 