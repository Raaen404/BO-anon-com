import os
import sys
import time
from stem import Signal
from stem.control import Controller
from stem.util import term
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
import schedule
import threading



with open('onionshare.auth_private', 'r') as f:
    line = f.readline()
    addr = line.split(':')[0]


onion_share_addr = 'http://'+addr+'.onion/upload'
#tor_proc = None


#Teksteditor
class TextEditor:
    def __init__(self, on_send):
        print("Initializing TextEditor")
        self.on_send = on_send
        self.window = tk.Tk()
        self.window.title("Text Editor")
        self.text_area = tk.Text(self.window, wrap=tk.WORD)
        self.text_area.pack(expand=tk.YES, fill=tk.BOTH)
        self.create_menu()
        self.window.protocol("WM_DELETE_WINDOW", self.close_editor)

    def create_menu(self):
        menu = tk.Menu(self.window)
        self.window.config(menu=menu)
        file_menu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Send Message", command=self.send_message)

    def send_message(self):
        if self.on_send:
            text_content = self.text_area.get(1.0, tk.END).strip()
            self.window.destroy()
            self.on_send(text_content)
            

    def start_editor(self):
        self.window.mainloop()

    def close_editor(self):
        if messagebox.askokcancel("Exit","Do you want to exit?"):
            self.window.destroy()


#Håndteringen av meldinger
class MessageHandler:
    def __init__(self, url):
        print("Initializing MessageHandler")
        self.url = url
        self.last_message = None
        self.scheduler = MessageScheduler(self)
        self.is_scheduled_send = False
        #self.start_tor()
        self.counter = 0


    '''def start_tor(self):
        global tor_proc
        print("Starting Tor with custom torrc")
        try:
            tor_proc = subprocess.Popen(["tor","-f","/home/raaen/BO/sender/custom_torrc"],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                        start_new_session=True)
        except Exception as e:
            print(f"Something went wrong: {e} ")
            if psutil.pid_exists(tor_proc.pid):
                tor_proc.kill()'''

    def new_message(self):
        print("new_message")
        self.is_scheduled_send = False
        print("Is message scheduled", self.is_scheduled_send)
        editor = TextEditor(on_send=self.handle_send)
        editor.start_editor()
    
    def handle_send(self, text):
        print("handle_send")
        self.last_message = text
        self.send_message_over_tor()


    def send_message_over_tor(self):
        print("send_message_over_tor")
        self.counter += 1
        print("Amount of times trying to send: ", self.counter)
        try: 
            files = {
                'text':(None, str(self.last_message))
            }

            with Controller.from_port(port = 9061) as controller:
                controller.authenticate(password='admin')
                controller.signal(Signal.NEWNYM)
                
                proxies = {
                    'http': 'socks5h://127.0.0.1:9060',
                    'https': 'socks5h://127.0.0.1:9060',
                }
                print("!"*86 + "\n\n")
                print("Sending message to OnionShare service\n\n")
                print("!"*86 + "\n\n")
                response = requests.post(self.url, proxies=proxies, files=files)
                if response.status_code==200:
                    print("Message was sent succesfully\n")
                    print("Message will be re-sent every half hour if another message isn't specified\n")
                    print("Taking you back to the main menu in 5 seconds...\n")
                    time.sleep(5)
                else:
                    print("Something went wrong when sending the message")
                    print("Taking you back to the main menu")
                    time.sleep(3)

        except Exception as e:
            print(f"An Error has occured: {e}")
            self.check_tor_connectivity()

        finally:
            if not self.is_scheduled_send:
                print("New Message is not scheduled for send. Scheduling message")
                self.scheduler.schedule_next_send()
        time.sleep(5)

    def check_tor_connectivity(self):
        print("check_tor_connectivity")
        counter = 0

        if counter < 5:
            tor_checker_url = 'http://check.torproject.org'
            print("Checking connection to the Tor Network\n")
            try:
                    with Controller.from_port(port = 9061) as controller:
                            controller.authenticate(password='admin')
                            #controller.signal(Signal.NEWNYM)

                    session = requests.session()
                    session.proxies = {'http': 'socks5h://127.0.0.1:9060',
                                        'https': 'socks5h://127.0.0.1:9060'}

                    response = session.get(tor_checker_url, proxies=session.proxies)
                    if response.status_code==200:
                        print(f"Response status code is: {response.status_code}. Connection to the Tor Network confirmed!\n\n")
                        print("Is the OnionShare service running?\n")
                        print("Taking you back to the main menu in 5 seconds...\n\n")
                        time.sleep(5)
                    
            except Exception as e:
                print(f"Error in confirming connection to the Tor Network. {e}")
                print("\n")
                print(f"Retrying connection to Tor Network in 30 seconds {counter}/5\n")
                counter += 1
                time.sleep(30)
                self.check_tor_connectivity()
            
        else:
            print("Max amount of connection attempts reached.\n")
            print("Do you have internet connection?")
            print("Taking you back to the main menu in 5 seconds.\n")
            time.sleep(5)


class MessageScheduler:
    def __init__(self, message_handler):
        print("Initializing MessageScheduler")
        self.message_handler = message_handler
        self.scheduled_job = None
        self.start_scheduler()
        
    def start_scheduler(self):
        print("Starting scheduler")
        self.thread = threading.Thread(target=self.run_continuously, daemon=True)
        self.thread.start()

    def schedule_next_send(self): 
        print("schedule_next_send")
        self.message_handler.is_scheduled_send = True
        if self.scheduled_job is not None:
            schedule.cancel_job(self.scheduled_job)
        print("Scheduling task!")
        self.scheduled_job = schedule.every(30).seconds.do(self.message_handler.send_message_over_tor)
        print("Job successfully scheduled")


    def run_continuously(self):
        while True:
            print("run_continuously")
            schedule.run_pending()
            time.sleep(1)

def main() -> None:
    #global tor_proc
    while True:
        with open('ascii-art-sender.txt', 'r') as f:
            print(''.join([line for line in f]))
            print("Options: ")
            print("-"*86)
            print("[1]: Send new message")
            print("[2]: Exit program")
            print("\n")
            print("What would you like to do?\n\n")
            print("In main")
        option = input()    
        match option:
            case "1":
                msg.new_message()
            case "2":
                print("\nExiting program...")
                #if psutil.pid_exists(tor_proc.pid):
                    #tor_proc.kill()
                sys.exit()
            case _:
                print("\nNot understood. Restarting...")
                time.sleep(2)
        time.sleep(0.1)

if __name__ == "__main__":
    msg = MessageHandler(onion_share_addr)
    main()

