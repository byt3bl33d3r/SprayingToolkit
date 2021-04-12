FROM python:3.7

WORKDIR /usr/src/SprayingToolkit
COPY . /usr/src/SprayingToolkit
ENV PATH="/usr/src/SprayingToolkit:${PATH}"

RUN apt-get -y update

RUN pip3 install -r requirements.txt

WORKDIR /host
ENTRYPOINT ["atomizer.py"]