#!/bin/sh
cd /docker-data/haruka-bot
nohup hb run &
sleep 5

cd /docker-data/go-cqhttp_123456-bot
nohup go-cqhttp &
sleep 5

cd /docker-data/go-cqhttp_234567-bot
nohup go-cqhttp &
sleep 5

cd /docker-data/go-cqhttp_56789-bot
nohup go-cqhttp &
sleep 5

service ssh start

echo
echo type [quit] if you want quit
read USER_INPUT
while [ "$USER_INPUT" != "quit" ];do
	read USER_INPUT
done