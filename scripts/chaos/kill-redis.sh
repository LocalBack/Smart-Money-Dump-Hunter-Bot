#!/bin/sh
docker stop redis
sleep 60
docker start redis
