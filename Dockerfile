FROM python:3

# WORKDIR /usr/src/Amazing

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD [ "ls" ]
# CMD [ "python3", "./main.py" ]