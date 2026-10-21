# C solver + Python automation (offline detection only: no screen, no uinput inside the container).
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libncurses-dev python3-venv python3-gi python3-tk \
        fonts-dejavu-core fonts-liberation fonts-freefont-ttf fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN make && make auto-setup

ENV TERM=xterm-256color
CMD ["./sudoku", "-h"]
