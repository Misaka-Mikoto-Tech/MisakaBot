#!/bin/sh
ps -e |grep go-cqhttp |awk '{print $1}'|xargs kill -2
ps -e |grep hb |awk '{print $1}'|xargs kill -2

