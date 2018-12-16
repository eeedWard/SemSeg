DROP DATABASE IF EXISTS dstest;
create database dstest;

# DROP USER IF EXISTS 'dstest'@'localhost' ;
# CREATE USER 'dstest'@'localhost' IDENTIFIED BY 'dstest';
# GRANT ALL ON dstest.* TO 'dstest'@'localhost';

DROP USER IF EXISTS 'dstest'@'%' ;
CREATE USER 'dstest'@'%' IDENTIFIED BY 'dstest';
GRANT ALL ON dstest.* TO 'dstest'@'%';

USE dstest;

source fake_db.sql;

source schema.sql;
