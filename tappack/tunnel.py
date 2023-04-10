import threading
from time import sleep

from pyngrok import ngrok


class Tunnel:

    def __init__(self, port):
        self.port = port
        self.is_open = True
        self.tunnel = None
        self.thread = threading.Thread(target=self.start_tunnel)
        self.start()

    def start(self):
        self.thread.start()
        while not self.tunnel:
            print('Waiting for tunnel to initialise...')
            sleep(1)

    def start_tunnel(self):
        self.tunnel = ngrok.connect(self.port)
        while self.is_open:
            sleep(1)
        ngrok.disconnect(self.tunnel.public_url)

    def close(self):
        print('Stopping thread. Tunnel should close.')
        self.is_open = False
        self.wait()

    def wait(self):
        while self.thread.is_alive():
            sleep(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


if __name__ == '__main__':
    pass
