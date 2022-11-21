import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from faker import Faker
import uuid
import random

load_dotenv()
# stored sensitive information in a .env file
MYSQL_HOSTNAME = os.getenv("MYSQL_HOSTNAME")
MYSQL_USER = os.getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

connection_string_azure = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOSTNAME}:3306/{MYSQL_DATABASE}'
db = create_engine(connection_string_azure)

print(db.table_names())

fake = Faker()

fake_patients = [
    {
        #keep just the first 8 characters of the uuid
        'mrn': str(uuid.uuid4())[:8],
        'first_name':fake.first_name(),
        'last_name':fake.last_name(),
        'zip_code':fake.zipcode(),
        'dob':(fake.date_between(start_date='-90y', end_date='-20y')).strftime("%Y-%m-%d"),
        'gender': fake.random_element(elements=('M', 'F')),
        'contact_mobile':fake.phone_number(),
        'contact_home':fake.phone_number()
    } for x in range(50)]

df_fake_patients = pd.DataFrame(fake_patients)
df_fake_patients = df_fake_patients.drop_duplicates(subset=['mrn'])



# Creating NDC Codes
ndc_codes = pd.read_csv('https://raw.githubusercontent.com/hantswilliams/FDA_NDC_CODES/main/NDC_2022_product.csv')
ndc_codes_1k = ndc_codes.sample(n=1000, random_state=1)
ndc_codes_1k = ndc_codes_1k.drop_duplicates(subset=['PRODUCTNDC'], keep='first')

# Creating CPT Codes
cpt_codes = pd.read_csv('https://gist.githubusercontent.com/lieldulev/439793dc3c5a6613b661c33d71fdd185/raw/25c3abcc5c24e640a0a5da1ee04198a824bf58fa/cpt4.csv')
cpt_codes_1k = cpt_codes.sample(n=1000, random_state=1)
cpt_codes_1k = cpt_codes_1k.drop_duplicates(subset=['com.medigy.persist.reference.type.clincial.CPT.code'], keep='first')

# Creating ICD-10 Codes
icd10codes = pd.read_csv('https://raw.githubusercontent.com/Bobrovskiy/ICD-10-CSV/master/2020/diagnosis.csv')
list(icd10codes.columns)
icd10codesShort = icd10codes[['CodeWithSeparator', 'ShortDescription']]
icd10codesShort_1k = icd10codesShort.sample(n=1000)
icd10codesShort_1k = icd10codesShort_1k.drop_duplicates(subset=['CodeWithSeparator'], keep='first')

# Creating LOINC Codes
loinccodes = pd.read_csv('data/loinc.csv')
list(loinccodes.columns)
loinccodesShort = loinccodes[['LOINC_NUM', 'COMPONENT']]
loinccodesShort_1k = loinccodesShort.sample(n=1000)
loinccodesShort_1k = loinccodesShort_1k.drop_duplicates(subset=['LOINC_NUM'], keep='first')



# Fake Patients
insertQuery = "INSERT INTO patients (mrn, first_name, last_name, dob, gender, contact_mobile, contact_home, zip_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)" ## %s indicates a dynamic value
for index, row in df_fake_patients.iterrows():
    db.execute(insertQuery, (row['mrn'], row['first_name'], row['last_name'], row['dob'], row['gender'], row['contact_mobile'], row['contact_home'], row['zip_code']))
    print("inserted row: ", index)

df = pd.read_sql_query("SELECT * FROM patients", db)



# ICD-10 Codes
insertQuery = "INSERT INTO conditions (icd10, description) VALUES (%s, %s)"
startingRow = 0
for index, row in icd10codesShort_1k.iterrows():
    startingRow += 1
    print('startingRow: ', startingRow)
    db.execute(insertQuery, (row['CodeWithSeparator'], row['ShortDescription']))
    print("inserted row db: ", index)
    ## stop once we have 100 rows
    if startingRow == 100:
        break

df = pd.read_sql_query("SELECT * FROM conditions", db)


# Medications
insertQuery = "INSERT INTO medications (ndc, generic, active_ingredients) VALUES (%s, %s, %s)"
medRowCount = 0
for index, row in ndc_codes_1k.iterrows():
    medRowCount += 1
    db.execute(insertQuery, (row['PRODUCTNDC'], row['PROPRIETARYNAME'], row['NONPROPRIETARYNAME']))
    print("inserted row: ", index)
    ## stop once we have 100 rows
    if medRowCount == 100:
        break
df = pd.read_sql_query("SELECT * FROM medications", db)


# Treatments and Procedures
insertQuery = "INSERT INTO treatment_procedures (cpt, description) VALUES (%s, %s)"
medRowCount = 0
for index, row in cpt_codes_1k.iterrows():
    medRowCount += 1
    db.execute(insertQuery, (row['com.medigy.persist.reference.type.clincial.CPT.code'], row['label']))
    print("inserted row: ", index)
    if medRowCount == 100:
        break
df = pd.read_sql_query("SELECT * FROM treatment_procedures", db)


# LOINC
insertQuery = "INSERT INTO social_determinants (loinc, description) VALUES (%s, %s)"
startingRow = 0
for index, row in loinccodesShort_1k.iterrows():
    startingRow += 1
    print('startingRow: ', startingRow)
    db.execute(insertQuery, (row['LOINC_NUM'], row['COMPONENT']))
    print("inserted row db: ", index)
    ## stop once we have 100 rows
    if startingRow == 100:
        break
df = pd.read_sql_query("SELECT * FROM social_determinants", db)


## Patient Conditions
df_conditions = pd.read_sql_query("SELECT icd10 FROM conditions", db)
df_patients = pd.read_sql_query("SELECT mrn FROM patients", db)

df_patient_conditions = pd.DataFrame(columns=['mrn', 'icd10'])
for index, row in df_patients.iterrows():
    df_conditions_sample = df_conditions.sample(n=random.randint(1, 5))
    df_conditions_sample['mrn'] = row['mrn']
    df_patient_conditions = df_patient_conditions.append(df_conditions_sample)

print(df_patient_conditions.head(20))

insertQuery = "INSERT INTO patient_conditions (mrn, icd10) VALUES (%s, %s)"

for index, row in df_patient_conditions.iterrows():
    db.execute(insertQuery, (row['mrn'], row['icd10']))
    print("inserted row: ", index)

df = pd.read_sql_query("SELECT * FROM patient_conditions", db)

## Patient Treatment and Procedures
df_treatment_procedures = pd.read_sql_query("SELECT cpt FROM treatment_procedures", db)
df_patients = pd.read_sql_query("SELECT mrn FROM patients", db)

df_patient_treatment_procedures = pd.DataFrame(columns=['mrn', 'cpt'])
for index, row in df_patients.iterrows():
    df_treatment_procedures_sample = df_treatment_procedures.sample(n=random.randint(1, 5))
    df_treatment_procedures_sample['mrn'] = row['mrn']
    df_patient_treatment_procedures = df_patient_treatment_procedures.append(df_treatment_procedures_sample)

print(df_patient_treatment_procedures.head(20))

insertQuery = "INSERT INTO patient_treatment_procedures (mrn, cpt) VALUES (%s, %s)"

for index, row in df_patient_treatment_procedures.iterrows():
    db.execute(insertQuery, (row['mrn'], row['cpt']))
    print("inserted row: ", index)

df = pd.read_sql_query("SELECT * FROM patient_treatment_procedures", db)

## Patient Social Determinants

df_social_determinants = pd.read_sql_query("SELECT loinc FROM social_determinants", db)
df_patients = pd.read_sql_query("SELECT mrn FROM patients", db)

df_patient_social_determinants = pd.DataFrame(columns=['mrn', 'loinc'])
for index, row in df_patients.iterrows():
    df_social_determinants_sample = df_social_determinants.sample(n=random.randint(1, 5))
    df_social_determinants_sample['mrn'] = row['mrn']
    df_patient_social_determinants = df_patient_social_determinants.append(df_social_determinants_sample)

print(df_patient_social_determinants.head(20))

insertQuery = "INSERT INTO patient_social_determinants (mrn, loinc) VALUES (%s, %s)"

for index, row in df_patient_social_determinants.iterrows():
    db.execute(insertQuery, (row['mrn'], row['loinc']))
    print("inserted row: ", index)

df = pd.read_sql_query("SELECT * FROM patient_social_determinants", db)
