FROM jschell12/pypy3:latest

WORKDIR /app

# Install dependencies
COPY ./requirements.txt /app/requirements.txt
COPY ./Makefile /app/Makefile
RUN make env_pypy3

# Copy application
COPY ./main.py /app/main.py
COPY ./lib /app/lib

# Copy scripts and configs
COPY ./etc/supervisord.conf /etc/supervisor/supervisord.conf
COPY ./scripts/command.sh /usr/bin/
COPY ./scripts/run.sh /app/run.sh
RUN chmod 700 /usr/bin/command.sh
RUN chmod 700 /app/run.sh


CMD ["supervisord", "-n", "--configuration", "/etc/supervisor/supervisord.conf"]