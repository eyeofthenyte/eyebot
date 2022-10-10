FROM python:3.9.1

RUN pip install -U discord.py
RUN pip install twitchio
RUN pip install gspread
RUN pip install gsheets

COPY . /opt/eyebot
WORKDIR /opt

CMD ["python", "eyebot/src/discord.py"]
