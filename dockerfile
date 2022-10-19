FROM python:3.10.7

RUN pip install -U discord.py
RUN pip install twitchio
RUN pip install gspread
RUN pip install gsheets
RUN pip install pyyaml

COPY . /opt/eyebot
WORKDIR /opt/eyebot

CMD ["python", "src/eyebot_discord.py"]
