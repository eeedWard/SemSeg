# Duckietown Challenges Server

[![Docker Hub](https://img.shields.io/docker/pulls/duckietown/dt-challenges-server.svg)](https://hub.docker.com/r/duckietown/dt-challenges-server)

This package contains the Duckietown Challenge Server.

It talks to the local DB.

Clients talk to this using a REST API. (Run the server to see the documentation.)

See also:

* [duckietown-challenges](http://github.com/duckietown/duckietown-challenges): 
  contains the "dt-challenges-executor" program which speaks to the server.
* [duckietown-shell-commands](http://github.com/duckietown/duckietown-shell-commands): 
  the "challenges" commands interface with this.

## Testing instructions 


### Set up database

Install MySQL.

Set up a fake DB for testing:

    $ cd db
    $ mysql -u root -p < init.sql

### Pre-requisites

You need Python 2.

### Install and run from source code 

Use the command `develop` to install the source code:

    $ python2 setup.py develop

(This assumes you run in a virtual environment; in other configurations you might need some variations.)

Run this command to check it is installed:

    $ python -c "import duckietown_challenges_server; print duckietown_challenges_server.__file__ "


To run:

    $ pserve --reload deployment/duckietown-server-local.ini

Open the url <http://localhost:6544> to see the interface.


### Install and run using Docker

Build:

    $ docker build -t my-server .

For Mac you can use:

    $ docker run -it -p 6544:6544 -v $PWD/deployment:deployment my-server pserve /deployment/duckietown-server-local-docker-mac.ini

For other OS, you need to make a similar `MYINIFILE.ini` file that contains your hostname in place of:

    duckietown_challenges_server.mysql_host = host.docker.internal

as the shortcut `host.docker.internal` does not work.

Then run:

    $ docker run -it -p 6544:6544 -v $PWD/deployment:deployment my-server pserve /deployment/MYINIFILE.ini


Open the url <http://localhost:6544> to see the interface.



### Set up testing environment

Then, set the environment variable `DTSERVER` as follows:

    $ export DTSERVER=http://localhost:6544
    
This environment variable is read by all the `dts challenges` commands.

It instructs them to use your local server instead of `challenges.duckietown.org`.

### Define a challenge

For the luck challenge:

    $ git clone git@github.com:duckietown/challenge-aido1_luck.git

Define as follows:

    $ cd challenges-aido1_luck/evaluation
    $ DTSERVER=http://localhost:6544 make define-challenge
    
### Make a submission

    $ cd challenges-aido1_luck/submission
    $ DTSERVER=http://localhost:6544 dts challenges submit
    
### Run an evaluator
    
This runs a continuous evaluator:
 
    $ DTSERVER=http://localhost:6544 dts challenges evaluator
    
### Development workflow

You can update the evaluation code and run `define-challenge` again to change the evaluation container.

To re-evaluate a particular submission, use:

    $ DTSERVER=http://localhost:6544 dts challenges evaluator --submission ID --reset
    
where `ID` is the ID of the submission.
  
  
## Configuration

### MySQL

The db info can be passed using `duckietown-server.ini`:

    duckietown_challenges_server.mysql_host = localhost
    duckietown_challenges_server.mysql_uid = dstest
    duckietown_challenges_server.mysql_pwd = dstest
    duckietown_challenges_server.mysql_db = dstest

or it can be passed in the following environment variables:

    DCS_MYSQL_HOST
    DCS_MYSQL_UID
    DCS_MYSQL_PWD
    DCS_MYSQL_DB

### AWS

    duckietown_challenges_server.s3_prefix = 'testing'
    duckietown_challenges_server.bucket_name = 'duckietown-ai-driving-olympics-1'
    duckietown_challenges_server.aws_access_key_id = 'xxx'
    duckietown_challenges_server.aws_secret_access_key = 'xxx'



    

