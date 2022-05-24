
import zmq 
import sys
import json
import os
import hashlib

CHUNK_SIZE = 1024*1
COMMANDS = ['upload', 'download', 'shared']

class Client:
    def __init__(self):
        
        self.command = ''
        self.content = b''
        self.file_name = ''
        self.file_hash = ''
        self.file_chunks = 0
        self.port_to_send = 0
        self.message = ''
        self.hash_torrent = ''

    def verify_command(self,command):
        if(command in COMMANDS):
            
            self.command = command
            # self.file_name = file_name
            return True
        else:
            return False

    def endoce(self):
        return [json.dumps({
            
            "file_name":self.file_name,
            "file_hash":self.file_hash,
            "file_chunks":self.file_chunks,
            "message":self.message
        }).encode('utf-8'), self.content]


def get_list_torrent():
    cont = os.listdir(os.getcwd()+"\\Control_Archivo")
    return cont


def get_number_interval(number:int):
    vaule = (pow(2,160))
    print(int((number%vaule)))

def write_file_segment(path, content, tipo):
    print(path)
    path = os.getcwd() + path + tipo
    # os.makedirs(self.name+'/files')
    print(path)     
    with open(path, 'w+') as file_segment:
        file_segment.writelines(content)
    return path

def read_file_segments(path, tipo = ''):
    with open(path + tipo, 'r') as file_segment:
        return [line.replace('\n','') for line in file_segment.readlines()]


def get_file_size(filename):
    st = os.stat(filename)
    return st.st_size

def get_file_hash(file):
    sha1 = hashlib.sha1()
    sha1.update(file)
    return sha1.hexdigest()

def get_file_segment_path(file_name):
    return '\\'+ 'Control_Archivo'+ '\\' + file_name
    # '/file_segments/'{}-{}'.format(user, file_name)

def find_port_hash(s,client,data_send):
    reply = ''

    while(reply != 'belongs'):
        s.connect('tcp://localhost:{}'.format(client.port_to_send ))
        s.send_multipart(data_send)
        m = s.recv_multipart()
        request = json.loads(m[0])
        reply = request['status']
        if(reply == 'continue_search'):
            s.disconnect('tcp://localhost:{}'.format(client.port_to_send ))
            client.port_to_send = request['port']
        else:
            s.disconnect('tcp://localhost:{}'.format(client.port_to_send ))



def main():
    client = Client()
    context = zmq.Context()
    s = context.socket(zmq.REQ)

    if(client.verify_command(command= sys.argv[1])):
        # try:
            if(client.command == 'upload'):
                client.file_name = input("Ingrese el nombre del archivo: ")
                client.port_to_send = 8001
                file_upload_progress = 1

                chunks_file = get_file_size(client.file_name)/CHUNK_SIZE 
                if(chunks_file != int(chunks_file)): 
                    chunks_file = int(chunks_file) + 1

                f = open(client.file_name, 'rb') 
                chunk = f.read(CHUNK_SIZE)

                file_segments = []

                while chunk:
                    if(chunks_file > 0):
                        print(str(int((file_upload_progress/chunks_file)*100))+'%')

                        client.file_hash = get_file_hash(chunk)
                        file_segments.append('{}\n'.format(client.file_hash))

                        data_send = [json.dumps({'message':'check_to_upload','hash':client.file_hash}).encode('utf-8'),b'']
                        find_port_hash(s,client,data_send)

                        client.content = chunk

                        s.connect('tcp://localhost:{}'.format(client.port_to_send ))
                        client.message = 'upload'
                        s.send_multipart(client.endoce())

                        ok = s.recv_multipart()
                        s.send_string("Dame id")
                        id_ser =s.recv_string()
                        # file_segments.append('{}{}{}\n'.format(client.file_hash, ', ', id_ser))
                        # file_segments.append('{}\n'.format(client.file_hash))                       
                        
                        s.disconnect('tcp://localhost:{}'.format(client.port_to_send ))

                        file_upload_progress += 1

                        chunk = f.read(CHUNK_SIZE)

                
                file_segment_path = get_file_segment_path(client.file_name)
                # client.hash_torrent = 
                               
                ruta = write_file_segment(file_segment_path, file_segments, '.torrent')

                client.hash_torrent = get_file_hash(str(ruta).encode('utf-8'))
                f.close()
                print('El archivo fue subido al servidor con exito')
                print("Comparta este link si desea que alguien descargue su archivo.\n")
                print(client.hash_torrent)

            if(client.command == 'download'):
                client.file_name = input("Ingrese el nombre del archivo: ")
                client.port_to_send = 8001
                client.message = 'download'
                file_segment_path = os.getcwd()+get_file_segment_path(client.file_name)                
               
                file_segments = read_file_segments(file_segment_path, '.torrent')

                path = os.getcwd()
                path = path+"//Descargas"+"//"+client.file_name
                fileWrite = open(path, 'wb')
                fileWrite.write(b'')
                fileWrite.close()

                for i in file_segments:
                    client.file_name = i+'.txt'
                    client.file_hash = i

                    data_send = [json.dumps({'message':'check_to_upload','hash':client.file_hash}).encode('utf-8'),b'']

                    find_port_hash(s,client,data_send)

                    s.connect('tcp://localhost:{}'.format(client.port_to_send ))
                    s.send_multipart(client.endoce())

                    ok = s.recv_multipart()

                    reply = json.loads(ok[0])

                    if(reply['message'] == 'ok-download'):
                        fileWrite = open(path, 'ab')    
                        fileWrite.write(ok[1])
                        fileWrite.close()                    

                    s.disconnect('tcp://localhost:{}'.format(client.port_to_send ))


            if(client.command == 'shared'):
                
                hash_tor =input("Ingrese el hash que le compartieron: ")
                ruta = os.getcwd()+"\\Control_Archivo\\"

                # ls_trr = []
                ls_trr = get_list_torrent()
                ls_hash_trr =[]
                print(ls_trr)
                
                for i in ls_trr:
                    content = get_file_hash(str(ruta + i).encode('utf-8'))
                    ls_hash_trr.append(content)
                    print(str(ruta+i))
                print(ls_hash_trr)
                n= 1
                for l in ls_hash_trr:
                    if l == hash_tor:
                        print("Se encontro en ",n)
                        n=n
                        break
                    else:
                        n += 1         
                print(n)
                file_founded = ls_trr[n-1]
                file_founded = file_founded.split(sep='.')
                print(file_founded)  
                file_name = str(file_founded[0]+"."+file_founded[1])
                print(file_name)
                
                client.file_name = file_name
                client.port_to_send = 8001
                client.message = 'download'
                file_segment_path = os.getcwd()+get_file_segment_path(client.file_name)                
               
                file_segments = read_file_segments(file_segment_path, '.torrent')

                path = os.getcwd()
                path = path+"//Descargas"+"//"+client.file_name
                fileWrite = open(path, 'wb')
                fileWrite.write(b'')
                fileWrite.close()

                for i in file_segments:
                    client.file_name = i+'.txt'
                    client.file_hash = i

                    data_send = [json.dumps({'message':'check_to_upload','hash':client.file_hash}).encode('utf-8'),b'']

                    find_port_hash(s,client,data_send)

                    s.connect('tcp://localhost:{}'.format(client.port_to_send ))
                    s.send_multipart(client.endoce())

                    ok = s.recv_multipart()

                    reply = json.loads(ok[0])

                    if(reply['message'] == 'ok-download'):
                        fileWrite = open(path, 'ab')    
                        fileWrite.write(ok[1])
                        fileWrite.close()                    

                    s.disconnect('tcp://localhost:{}'.format(client.port_to_send ))
                print("Archivo compartido descargado con exito")
        # except OSError:
        #     print('Problema con el archivo')
        #     return 0
    else:
        print('El comando no existe')


if __name__ == "__main__":
    main()
