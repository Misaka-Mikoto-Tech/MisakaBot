#!/bin/sh
cd /docker-data/go-cqhttp
nohup go-cqhttp &
cd /docker-data/haruka-bot
nohup hb run &