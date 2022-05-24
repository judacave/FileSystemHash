import zmq
import json
import os
import sys
import glob
import random
import string
import hashlib

COMMANDS = ['first', 'connect']

# UTILS------------------------------------

def random_string():
    chars = string.ascii_lowercase
    return ''.join((random.choice(chars)) for x in range(30))

def hash_string(cadena):
    h = hashlib.sha1()
    h.update(cadena.encode('utf-8'))
    hexa = h.hexdigest()
    return int(hexa, 16)

def upload(folder_name, re, byte_content):
    file_hash = re['file_hash']
    path = folder_name+'/files/{}.txt'.format(file_hash)
    message = add_file(path, byte_content)
    return message

def add_file(path, byte_content):
    file = open(path, 'wb+')
    file.write(byte_content)
    file.close()
    return [{'message': 'ok'}]

def download(folder_name, file_name):
    # path = folder_name+'/files/{}'.format(file_name)
    path = folder_name + "//files//" + file_name

    try:
        file = open(path, 'rb')
        content = file.read()
        file.close()
        return [{'message': 'ok-download'}, content]
    except:
        return [{
                'message': 'message',
                're': 'El archivo no existe'
            }, b'']

class Folder_Controller:

    def __init__(self, folder_name):
        self.name = str(folder_name)
        self.__create_folder()

    def __create_folder(self):
        os.makedirs(self.name+'/files')
        os.makedirs(self.name+'/data')
        self.__init_intervals_file()
    
    def __init_intervals_file(self):
        with open(self.name+'/data/interval.json', 'w+') as file:
            data = {}         
            json.dump(data, file)

class Server:
    def __init__(self):
        self.command = ''
        self.port_server = ''
        self.port_reply = '8001'
        self.port_request = '8001'
        self.id = 0
        self.id_reply = 0
        self.id_request = 0
        self.interval = {}
        self.folder_controller = None

    def __init_folder_controller(self):
        self.folder_controller = Folder_Controller(self.id)

    def verify_command(self, command):
        if(command in COMMANDS):
            self.command = command
            return True
        else:
            return False

    def create_first(self, port_server, id_server):
        self.port_server = str(port_server)
        self.id = id_server
        self.__init_folder_controller()
        return True

    def assign_connection(self, port_server, port_reply, port_request, id_server):
        self.port_server = port_server
        self.port_reply = port_reply
        self.port_request = port_request
        self.id = id_server
        self.__init_folder_controller()
        return True

    def check_id(self):
        control_check_id = True
        port_temp = int(self.port_reply)

        while control_check_id:

            s.connect('tcp://localhost:{}'.format(port_temp))
            data = json.dumps(
                {'message': 'check-id', 'id_server': self.id}).encode('utf-8')

            s.send_multipart([data, b''])

            reply = s.recv_multipart()
            re = json.loads(reply[0])

            if(re['ok'] == 'accepted'):
                control_check_id = False

                self.port_request = str(re['port'])
                self.port_reply = str(port_temp)

                s.disconnect('tcp://localhost:{}'.format(port_temp))

            elif(re['ok'] == 'rejected'):

                if(int(re['port']) == 8001):
                    control_check_id = False

                    self.port_request = str(port_temp)
                    self.port_reply = str(re['port'])

                s.disconnect('tcp://localhost:{}'.format(port_temp))
                port_temp = int(re['port'])

    def create_interval(self):

        self.interval['intervals'] = []

        if(self.command == 'first'):
            max_interval = pow(2, 160) - 1
            print("ID Server:", max_interval)
            self.id_reply = max_interval
            self.interval['intervals'].append(
                [int(self.id_request), max_interval])

        if(self.command == 'connect'):

            self.interval['intervals'] = []
            self.interval['intervals'].append(
                [int(self.id_request), int(self.id) - 1])
            self.id_reply = int(self.id) - 1

        path = self.folder_controller.name + '/data/interval.json'
        with open(path, 'w+') as file:
            data = {}
            data['intervals'] = server.interval['intervals']
            data['port_origin'] = server.port_server
            data['port_destiny'] = server.port_reply
            json.dump(data, file)

    def create_connection_reply(self, s,):
        s.connect('tcp://localhost:{}'.format(self.port_reply))
        print(self.port_reply)
        data = json.dumps({'message': 'create-connection-reply',
                          'id_server': self.id, 'port': self.port_server}).encode('utf-8')

        s.send_multipart([data, b''])
        reply = s.recv_multipart()
        re = json.loads(reply[0])
        files_bytes_list = reply[1:]

        s.disconnect('tcp://localhost:{}'.format(self.port_reply))

        for file_name, content in zip(re['non_range_files'], files_bytes_list):
            path = self.folder_controller.name+'/files/{}'.format(file_name)
            add_file(path, content)

    def create_connection_request(self, s,):
        s.connect('tcp://localhost:{}'.format(self.port_request))
        data = json.dumps({'message': 'create-connection-request',
                          'port': self.port_server}).encode('utf-8')
        s.send_multipart([data, b''])
        reply = s.recv_multipart()

        re = json.loads(reply[0])
        server.id_request = re['id_server']
        print(re['ok'])
        server.create_interval()

        s.disconnect('tcp://localhost:{}'.format(self.port_request))

    def check_intervals(self, hash):
        dec = int(hash, 16)
        value = (pow(2, 160))
        value = (int((dec % value)))

        if(value >= self.interval['intervals'][0][0] and value <= self.interval['intervals'][0][1]):
            return True
        return False

    def delete_file_with_name(self, file_name):
        path = self.folder_controller.name+'/files/'+file_name
        if os.path.exists(path):
            os.remove(path)
            return True
        else:
            print("The file does not exist")
            return False

    def get_file_with_name(self, file_name):
        path = self.folder_controller.name+'/files/'+file_name
        file = open(path, 'rb')
        return file

    def get_files_list(self):
        path = self.folder_controller.name+'/files/*.txt'
        return glob.glob(path)

    def get_non_in_range_files(self):
        files_list = self.get_files_list()
        non_range_files_list = []  # Lista de archivos que no pertenecen al intervalo
        for file_path in files_list:
            file_name = os.path.split(file_path)[1]
            file_hash = file_name.split('.')[0]
            if not server.check_intervals(file_hash):
                non_range_files_list.append(file_name)
        return non_range_files_list


count = 0
context = zmq.Context()
command = sys.argv[1]


if(command == 'first'):
    s = context.socket(zmq.REP)
elif(command == 'connect'):
    s = context.socket(zmq.REQ)
    
control = True
server = Server()

if(server.verify_command(command=command)):

    
    if(command == 'first'):
        port_server = 8001
        server.create_first(port_server=8001, id_server=0)
        
        server.create_interval()

    if(command == 'connect'):
        port_server = input("Ingrese el puerto: ")
        number_interval = hash_string(random_string())
        
        server.id = number_interval
        print("ID Server:", number_interval)
        server.check_id()
        server.assign_connection(port_server=port_server, port_reply=server.port_reply,
                                 port_request=server.port_request, id_server=number_interval)
                                 
        server.create_connection_request(s=s)
        server.create_connection_reply(s=s)



else:
    control = False

s = context.socket(zmq.REP)
s.bind('tcp://*:{}'.format(port_server))


while control:

    print('\nEsperando solicitud {}\n\n'.format(count))
    count = count + 1

    m = s.recv_multipart()
    request = json.loads(m[0])

    if(request['message'] == 'check-id'):
        if(int(server.id) > int(request['id_server'])):
            print('Peticion aceptada')
            data_send = [json.dumps(
                {'ok': 'accepted', 'port': server.port_request}).encode('utf-8'), b'']
        else:
            print('Peticion rechazada')
            data_send = [json.dumps(
                {'ok': 'rejected', 'port': server.port_reply}).encode('utf-8'), b'']
        s.send_multipart(data_send)

    if(request['message'] == 'create-connection-reply'):
        server.port_request = request['port']
        server.id_request = request['id_server']

        server.create_interval()

        non_in_range_files = server.get_non_in_range_files()  

        bytes_array = []

        for file_name in non_in_range_files:

            file = server.get_file_with_name(file_name)
            bytes_array.append(file.read())
            file.close()

        data_send = [json.dumps(
                {
                    'ok': 'El intervalo fue actualizado',
                    'non_range_files': non_in_range_files
                }).encode('utf-8'),*bytes_array]
        
        print(len(data_send))

        s.send_multipart(data_send)

        for file_name in non_in_range_files:
            server.delete_file_with_name(file_name)
        

    if(request['message'] == 'create-connection-request'):
        server.port_reply = request['port']

        data_send = [json.dumps(
            {'ok': 'ID fue enviado', 'id_server': server.id}).encode('utf-8'), b'']
        print('El id fue enviado al {}'.format(server.port_reply))
        server.create_interval()

        s.send_multipart(data_send)

    if(request['message'] == 'check_to_upload'):

        message_client = request['hash']
        control_upload = server.check_intervals(message_client)

        if(control_upload):
            data_send = [json.dumps(
                {'status': 'belongs', }).encode('utf-8'), b'']
            print('El archivo pertenece')
            s.send_multipart(data_send)
        else:
            data_send = [json.dumps(
                {
                    'status': 'continue_search',
                    'port': server.port_reply
                }).encode('utf-8'), b'']
            print('continuar la busqueda')
            s.send_multipart(data_send)

    if request['message'] == 'upload':
        
        message = upload(folder_name=server.folder_controller.name,re=request, byte_content=m[1])
        id = server.id
        data_send = [json.dumps(message[0]).encode('utf-8'), b'']
        s.send_multipart(data_send)
        s.recv_string()
        s.send_string(str(id))

    if request['message'] == 'download':
        file_name = request['file_name']
        message = download(folder_name=server.folder_controller.name,file_name=request['file_name'])
        byte_content = message[1]
        resp = message[0]
        s.send_multipart([json.dumps(resp).encode('utf-8'), byte_content])