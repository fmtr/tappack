FROM edwardbrown/python

RUN pip install pip --upgrade
WORKDIR /usr/src/fm
COPY . /usr/src/fm

RUN pip install .[server]
RUN ngrok version