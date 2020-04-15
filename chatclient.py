import socket

import sys
import traceback

from PyQt5.QtWidgets import QApplication, QInputDialog, QHBoxLayout, QWidget, QPushButton, QTextEdit, \
    QVBoxLayout, QLineEdit, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal


class App():
    def __init__(self):
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.q_app = QApplication([])


        #Buttons
        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.create)

        self.join_button = QPushButton("Join")
        self.join_button.clicked.connect(self.join)

        self.leave_button = QPushButton("Leave")
        self.leave_button.clicked.connect(self.end)

        self.clear_button = QPushButton("Clear Text")
        self.clear_button.clicked.connect(self.clear)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.join_button)
        button_layout.addWidget(self.leave_button)
        button_layout.addWidget(self.clear_button)


        #Communication Area
        self.received = QTextEdit()
        self.received.insertHtml("<b><u>Welcome to ChatRoom MK 457!<b><u>")
        self.received.insertPlainText("\n")
        self.received.setReadOnly(True)

        self.m_text = MessageBox(self.send)


        self.m_button = QPushButton("Send")
        self.m_button.clicked.connect(self.send)

        send_text_layout = QHBoxLayout()
        send_text_layout.addWidget(self.m_text)
        send_text_layout.addWidget(self.m_button)

        send_receive_layout = QVBoxLayout()
        send_receive_layout.addWidget(self.received)
        send_receive_layout.addLayout(send_text_layout)

        #All GUI elements
        full_layout = QHBoxLayout()
        full_layout.addLayout(send_receive_layout)
        full_layout.addLayout(button_layout)


        self.window = QWidget()
        self.window.setLayout(full_layout)
        self.window.setWindowTitle("ChatRoom MK 457")
        self.window.show()

    #Used for creating a room
    def create(self):
        print("Attempting to host!")
        port_no, status = QInputDialog().getText(self.window, "Create", "Desired Port Number", QLineEdit.Normal)

        if status and (not port_no.isdigit() or not (int(port_no) >= 1024 and int(port_no) <= 65535) ):
            self.create()
        elif status and port_no:
            self.connected = True

            try:
                self.socket.bind(("0.0.0.0", int(port_no)))
                self.socket.listen()

                partner, sock_accept = self.socket.accept()
                self.socket.close()
                self.socket = partner

                self.received.insertHtml("""<font color="green"><b><u>You're in!</b></u></font>""")
                self.received.insertPlainText("\n-----------\n")

                self.listen = Listener(partner)
                self.listen.start()

                self.listen.finished.connect(self.close)
                self.listen.chat_signal.connect(self.m_create)

            except:
                self.connected = False
                traceback.print_exc(file=sys.stdout)

    #Used for joining a room
    def join(self):
        print("Attempting to join!")

        host, status = QInputDialog().getText(self.window, "Join", "IP:Port", QLineEdit.Normal)

        host_ip = host.split(":")
        if host_ip[0] == "":
            host_ip[0] = "127.0.0.1"

        if status and not(1024 <= int(host_ip[1]) <= 65535):
            self.join()

        elif status and host:
            try:
                self.socket.connect((host_ip[0], int(host_ip[1])))
                self.received.insertHtml("""<font color="green"><b><u>You're in!</b></u></font>""")
                self.received.insertPlainText("\n-----------\n")

                self.connected = True

                self.listen = Listener(self.socket)
                self.listen.start()
                self.listen.finished.connect(self.close)
                self.listen.chat_signal.connect(self.m_create)

            except Exception:
                traceback.print_exc(file=sys.stdout)

    #Used to close a connection
    def close(self):
        self.received.insertHtml("<b><u>Chat ended!</b></u>")
        self.received.insertPlainText("\n")
        self.socket.close()
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Used to send messages
    def send(self):
        if self.connected:
            self.received.insertHtml("""<font color="blue"><b>You:</b> """+self.m_text.text()+"""</font""")
            self.received.insertPlainText("\n")

            self.socket.sendall(("""<font color="red"><b>Partner:</b> """+self.m_text.text()+"""</font""").encode())
            self.m_text.setText("")
        else:
            QMessageBox.question(self.window, 'Oops!', "You are not connected to any chatroom",
                                 QMessageBox.Ok,
                                 QMessageBox.Cancel)
            self.m_text.setText("")

    #Used to formulate a message
    def m_create(self, m):
        self.received.insertHtml(m)
        self.received.insertPlainText("\n")

    #Used to terminate a chat
    def end(self):
        if self.connected:
            self.socket.sendall("<<<END CONNECTION>>>".encode())
        else:
            QMessageBox.question(self.window, 'Oops!', "You are not connected to any chatroom",
                                               QMessageBox.Ok,
                                               QMessageBox.Cancel)
    #Clears the message box
    def clear(self):
        buttonReply = QMessageBox.question(self.window, 'WARNING', "Do you want to clear all text?",
                                           QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                           QMessageBox.Cancel)
        if buttonReply == QMessageBox.Yes:
            self.received.setText("")




#Overwrites a method in QThread
class Listener(QThread):

    chat_signal = pyqtSignal(object)

    def __init__(self, socket):
        QThread.__init__(self)
        self.socket = socket

    def run(self):
        with self.socket:
            while(True):
                try:
                    message = self.socket.recv(20480).decode()
                except:
                    self.socket.close()
                    traceback.print_exc(file=sys.stdout)
                if message == "<<<END CONNECTION>>>":
                    self.socket.sendall("<<<END CONNECTION>>>".encode())
                    self.socket.close()
                    break
                self.chat_signal.emit(message)
        print("Terminated connection.")

#Used for sending a message
class MessageBox(QLineEdit):
    def __init__(self, callback):
        self.enter_callback = callback
        super().__init__()

#Begin the program
chat_app = App()
chat_app.q_app.exec_()
chat_app.socket.close()