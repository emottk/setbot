FROM python:3.7-stretch
ENV PYTHONUNBUFFERED 1

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

COPY . .

ENTRYPOINT ["flask"]
CMD ["run", "-h", "0.0.0.0"]

