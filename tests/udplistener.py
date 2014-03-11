# !/usr/bin/python
#-*- coding: utf-8 -*-

import select
import socket 

port = 21000  # where do you expect to get a msg?
bufferSize = 1024 # whatever you need

#data = r"\xe6\x9a\x00\x01\x00\xff\xffn&\x002\x00\x9d\x00\xd4\x00w\x0e\x00\x00\x00\x00\x00\x00\x00\x00:\x00;\x00\xb3\x01:\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x01\x00\x92\x00\x10\x00\x00\x01\x11\x10\x11\x11\x00\x01\x00\x00\x10\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x000\x12\x00\x10\x00\x00\x01\x11\x10\x11\x11\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x10\x00\x01\x01\x01\x00\x00\x00\x00\x10\x11\x11\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x11\x00\x01"
#data2 = data.split('\\x')
#print data2

class Server:
 
    # Contructeur de la class Server.
    #
    # @param port Port de connexion
    # @param listen Nombre de connexion en attente max
    def __init__(self, port = 21000, listen = 5):
        # Initialisation of attr
        self.nbClients = 0	# Nombre de client connecté
        self.sockets = []	# Liste des sockets client
 
        # Création du socket serveur
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # On passe le socket serveur en non-bloquant
        self.socket.setblocking(0)
        # On attache le socket au port d'écoute. 
        self.socket.bind(('', port))
        # On lance l'écoute du serveur. "listen" est le nombre max de 
        # connexion quand la file d'attente
        self.socket.listen(listen)
        print "server initalisé"
 
 
 
    # Surcouche de la fonction socket.recv
    # On utilise le système d'exeption de recv pour savoir si il reste
    # des donnees a lire
    #
    # @param socket Socket sur lequelle il faut recuperer les données
    # @return Données envoyées par le client
    def receive(self, socket):
        buf = "" # Variable dans laquelle on stocke les données
        _hasData = True # Nous permet de savoir si il y de données à lire
        print 'server : data recues'
        while _hasData:
            # On passe le socket en non-bloquant
            socket.setblocking(0)
            try:
                _data = socket.recv(256)
                if(_data):
                    buf += _data
                else:
                    # Déconnexion du client
                    _hasData = False
            except:
                _hasData = False
        return buf

	# Fonction qui lance les sockets et s'occupe des clients
    def run(self):
        # On ajoute le socket serveur à la liste des sockets
        self.sockets.append(self.socket)
        print 'server started'
        while True:
            print "select.select"
            try:
                # La fonction select prends trois paramètres qui sont la liste des sockets
                # Elle renvoie 3 valeurs
                # 	1- La liste des sockets qui ont reçus des données
                # 	2- La liste des sockets qui sont prêt à envoyer des données
                #	3- Ne nous interesse pas dans notre cas
                readReady ,writeReady, nothing = select.select(self.sockets, self.sockets, [])
            except select.error, e:
                break
            except socket.error, e:
                break
            print 'parcours socket'
            # On parcours les sockets qui ont reçus des données
            for sock in readReady:
                if sock == self.socket:
                    # C'est le socket serveur qui a reçus des données
                    # Cela signifie qu'un client vient de se connecter
                    # On accept donc ce client et on récupère qques infos
                    client, address = self.socket.accept()
                    # On incrémente le nombre de connecté
                    self.nbClients += 1
                    # On ajoute le socket client dans la liste des sockets
                    self.sockets.append(client)
                else:
                    # Le client a envoyé des données, on essaye de les lire
                    try:
                        # On fait appelle à la surchage que l'on a écrite plus haut
                        data = self.receive(sock)
                        if data:
                            # On renvoi au client ce qu'il a envoyé
                            sock.send(data)
                        else:
                            # Si data est vide c'est que le client s'est déconnecté
                            # On diminu le nombre de client
                            self.nbClients -= 1
                            # On supprime le socket de la liste des sockets
                            self.sockets.remove(sock)
                    except socket.error, e:
                        self.sockets.remove(sock)

if __name__ == "__main__":
    server = Server(port, 5)
    server.run()
