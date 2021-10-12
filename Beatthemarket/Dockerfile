# Base Image
FROM python:3.9.6
ENV PYTHONUNBUFFERED=1

# create and set working directory
WORKDIR /code
COPY requirements.txt /code/

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade pip setuptools wheel

RUN pip3 install -r requirements.txt

RUN pip install markdown
RUN pip install django-filter
RUN pip install tqdm

ENV TZ Asia/Hong_Kong

# Ta Lib
# WORKDIR /var
# RUN tar -xzf ta-lib-0.4.0-src.tar.gz
# RUN cd ta-lib/
# RUN ./configure --prefix=/usr
# RUN make
# RUN sudo make install
# pip install ta-lib