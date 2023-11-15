FROM python:3.11.6-bookworm

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -U pip setuptools wheel
RUN pip install --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \ 
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get install -y ffmpeg curl google-chrome-stable

COPY . .

CMD [ "python", "./memebot.py" ]