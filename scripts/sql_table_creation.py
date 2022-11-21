import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

def droppingFunction_limited(dbList, db_source):
    for table in dbList:
        if table.startswith('production_') == False:
            db_source.execute(f'drop table {table}')
            print(f'dropped table {table}')
        else:
            print(f'kept table {table}')

def droppingFunction_all(dbList, db_source):
    for table in dbList:
        db_source.execute(f'drop table {table}')
        print(f'dropped table {table} succesfully!')
    else:
        print(f'kept table {table}')

load_dotenv()

# stored sensitive information in a .env file
MYSQL_HOSTNAME = os.getenv("MYSQL_HOSTNAME")
MYSQL_USER = os.getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

connection_string_azure = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOSTNAME}:3306/{MYSQL_DATABASE}'
db = create_engine(connection_string_azure)

disable_foreign_key = """
SET FOREIGN_KEY_CHECKS=0
;
"""
reenable_foreign_key = """
SET FOREIGN_KEY_CHECKS=1
;
"""
db.execute(disable_foreign_key)
droppingFunction_all(db.table_names(), db)
db.execute(reenable_foreign_key)
print(db.table_names())

table_patients = """
create table if not exists patients (
    id int auto_increment,
    mrn varchar(255) default null unique,
    first_name varchar(255) default null,
    last_name varchar(255) default null,
    zip_code varchar(255) default null,
    dob varchar(255) default null,
    gender varchar(255) default null,
    contact_mobile varchar(255) default null,
    contact_home varchar(255) default null,
    PRIMARY KEY (id)
);
"""

table_medications = """
create table if not exists medications (
    id int auto_increment,
    ndc varchar(255) null unique,
    generic varchar(255) default null,
    active_ingredients varchar(255) default null,
    PRIMARY KEY (id)
);
"""

table_treatments_procedures = """
create table if not exists treatment_procedures (
    id int auto_increment,
    cpt varchar(255) null unique,
    description varchar(255) default null,
    PRIMARY KEY (id)
);
"""

table_conditions = """
create table if not exists conditions (
    id int auto_increment,
    icd10 varchar(255) null unique,
    description varchar(255) default null,
    PRIMARY KEY (id)
);
"""

table_social_determinants = """
create table if not exists social_determinants (
    id int auto_increment,
    loinc varchar(255) null unique,
    description varchar(255) default null,
    PRIMARY KEY (id)
);
"""

table_patient_medications = """
create table if not exists patient_medications (
    id int auto_increment,
    mrn varchar(255) default null,
    ndc varchar(255) default null,
    PRIMARY KEY (id),
    FOREIGN KEY (mrn) REFERENCES patients(mrn) ON DELETE CASCADE,
    FOREIGN KEY (ndc) REFERENCES medications(ndc) ON DELETE CASCADE
);
"""

table_patient_conditions = """
create table if not exists patient_conditions (
    id int auto_increment,
    mrn varchar(255) default null,
    icd10 varchar(255) default null,
    PRIMARY KEY (id),
    FOREIGN KEY (mrn) REFERENCES patients(mrn) ON DELETE CASCADE,
    FOREIGN KEY (icd10) REFERENCES conditions(icd10) ON DELETE CASCADE
);
"""

table_patient_social_determinants = """
create table if not exists patient_social_determinants (
    id int auto_increment,
    mrn varchar(255) default null,
    loinc varchar(255) default null,
    PRIMARY KEY (id),
    FOREIGN KEY (mrn) REFERENCES patients(mrn) ON DELETE CASCADE,
    FOREIGN KEY (loinc) REFERENCES social_determinants(loinc) ON DELETE CASCADE
);
"""

table_patient_treatments = """
create table if not exists patient_treatment_procedures (
    id int auto_increment,
    mrn varchar(255) default null,
    cpt varchar(255) default null,
    PRIMARY KEY (id),
    FOREIGN KEY (mrn) REFERENCES patients(mrn) ON DELETE CASCADE,
    FOREIGN KEY (cpt) REFERENCES treatment_procedures(cpt) ON DELETE CASCADE
);
"""

table_accounts = """
CREATE TABLE IF NOT EXISTS `accounts` (
	`id` int(11) NOT NULL AUTO_INCREMENT,
    `username` varchar(50) NOT NULL,
    `password` varchar(255) NOT NULL,
    `email` varchar(100) NOT NULL,
    `account_type` varchar(50) NOT NULL,
    `mrn` varchar(50) NULL,
    `date_created` datetime NULL,
    `last_login` datetime NULL,
    PRIMARY KEY (`id`)
);
INSERT INTO `accounts` (`id`, `username`, `password`, `email`, `account_type`) VALUES (1, 'admin', 'admin', 'admin@admin.com', 'admin');
"""

db.execute(table_patients)
db.execute(table_medications)
db.execute(table_treatments_procedures)
db.execute(table_conditions)
db.execute(table_social_determinants)
db.execute(table_patient_medications)
db.execute(table_patient_treatments)
db.execute(table_patient_conditions)
db.execute(table_patient_social_determinants)

# confirm if script is working
print(db.table_names())
