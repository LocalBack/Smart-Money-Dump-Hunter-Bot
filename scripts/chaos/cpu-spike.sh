#!/bin/sh
docker exec orchestrator sh -c 'yes > /dev/null & pid=$!; sleep 20; kill $pid'
