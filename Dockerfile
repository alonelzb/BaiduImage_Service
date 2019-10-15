FROM python
MAINTAINER zbluo "alonelzb2@gmail.com"
RUN mkdir /luozaibo
COPY . /luozaibo/
WORKDIR /luozaibo
RUN pip3 install -r requirements.txt
EXPOSE 5000
CMD python3 app.py
