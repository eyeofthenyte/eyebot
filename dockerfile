FROM python:3.9.1

RUN pip install -U discord.py
RUN pip install gspread

COPY . /opt/eyebot
WORKDIR /opt

CMD ["python", "eyebot/eyebot.py"]
