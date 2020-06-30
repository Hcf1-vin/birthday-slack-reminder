FROM python:3

RUN mkdir /app
WORKDIR /app

COPY /src .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT [ "python","/app/main.py" ]