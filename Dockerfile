ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python packages on system level --> PEP668
ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update
RUN apt-get install python3 -y \
    python3-pip -y \
    git -y \
    imagemagick -y

RUN pip install flask flask-cors playwright

RUN playwright install --with-deps chromium

COPY server.py /

RUN git clone https://github.com/NaitLee/Cat-Printer 
WORKDIR /Cat-Printer
RUN pip install -r requirements.txt

WORKDIR  /
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]