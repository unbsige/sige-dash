FROM python:3.11.2-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    software-properties-common \
    git \
    cron \
    apt-get autoremove -y &&\
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*


RUN git clone https://github.com/unbsige/sige-dash .

RUN pip install -r requirements.txt

ENTRYPOINT [ "streamlit", "run", "app.py", "--server.port", "80", "server.address", "0.0.0.0"]" ]
