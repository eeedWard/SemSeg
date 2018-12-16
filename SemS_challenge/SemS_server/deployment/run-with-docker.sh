#!/usr/bin/env bash

docker run -it  \
    -p 6543:6543/tcp \
    -v $PWD:/config \
    duckietown/dt-challenges-server:v2 \
    pserve /config/duckietown-server-dorothy.ini
