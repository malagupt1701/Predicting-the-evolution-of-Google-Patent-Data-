#!/usr/bin/env python
# coding: utf-8

# In[2]:


import xmltodict
import os
import pandas as pd
import time
import boto3
import shutil


# In[3]:


def dataframe_generator(partition):
    countries = []
    doc_numbers = []
    dates=[]
    utilities = []
    
    titles=[]
    org_names=[]
    org_cities=[]
    org_countries=[]
    
    nois = []
    abstracts=[]
    
    
    files = os.listdir('Unzipped/{}'.format(partition))
    for file in files: 
        with open(f'Unzipped/{partition}/{file}') as f:
            try:
                dic=xmltodict.parse(f.read())
                countries.append(dic['us-patent-application']['us-bibliographic-data-application']['application-reference']['document-id']['country'])
                doc_numbers.append(dic['us-patent-application']['us-bibliographic-data-application']['application-reference']['document-id']['doc-number'])
                dates.append(dic['us-patent-application']['us-bibliographic-data-application']['application-reference']['document-id']['date'])
                utilities.append(dic['us-patent-application']['us-bibliographic-data-application']['application-reference']['@appl-type'])
                titles.append(dic['us-patent-application']['us-bibliographic-data-application']['invention-title']['#text'])
                try:
                    org_names.append(dic['us-patent-application']['us-bibliographic-data-application']['us-parties']['us-applicants']['us-applicant']['addressbook']['orgname'])
                except:
                    org_names.append(np.nan)
                try:
                    org_cities.append(dic['us-patent-application']['us-bibliographic-data-application']['us-parties']['us-applicants']['us-applicant']['addressbook']['address']['city'])
                except:
                    org_cities.append(np.nan)
                try:    
                    org_countries.append(dic['us-patent-application']['us-bibliographic-data-application']['us-parties']['us-applicants']['us-applicant']['addressbook']['address']['country'])
                except:
                    org_countries.append(np.nan)

                nois.append(len(dic['us-patent-application']['us-bibliographic-data-application']['us-parties']['inventors']['inventor']))
                abstracts.append(dic['us-patent-application']['abstract']['p']['#text'])
            except:
                continue
        
    
    df = pd.DataFrame(list(zip(doc_numbers, titles, utilities, dates, countries, org_names, org_cities, org_countries, nois, abstracts)),
               columns =['Doc_number', 'Title', 'Type','App_Date','Country','Org_Name','Org_City','Org_Country','No_inventors','Abstract'])
    
    df['App_Date'] = pd.to_datetime(df['App_Date'])
    
    return df


# In[4]:


access_key_id  = '------'
secret_access_key = '------'

session = boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
resources = session.resource('s3')

s3 = session.client('s3')
my_bucket = resources.Bucket('capstone-storage')


# In[15]:


response = s3.list_objects_v2(Bucket='capstone-storage')
files = response.get("Contents")


# In[36]:


locs = []

for file in files:
    if file['Key'].endswith('.zip'):
        locs.append(file['Key'])


# In[21]:


updated_locs = []
for loc in locs:
    file_name = loc.split('/')[2]
    if len(file_name.split('_'))>1 and file_name.endswith('.zip'):
        updated_locs.append(file_name.split('_')[0]+'.zip')
    elif file_name.endswith('.zip'):
        updated_locs.append(file_name)
    else:
        continue


# In[35]:


for loc,uloc in zip(locs,updated_locs):
    year = loc.split('/')[1]
    out_file = loc.split('/')[2] #has zip tag
    s3.download_file('capstone-storage',loc,Filename='unzipped/'+out_file)
    os.system('unzip unzipped/{} -d unzipped'.format(out_file))
    os.system('python3 parse_patents.py -i unzipped/{}.xml'.format(uloc[:-4]))
    os.remove('unzipped/{}.xml'.format(uloc[:-4]))
    os.remove('unzipped/{}'.format(out_file))
    df = dataframe_generator(uloc[:-4])
    shutil.rmtree('Unzipped/{}'.format(uloc[:-4]))
    df.to_csv('unzipped/{}.csv'.format(uloc[:-4]))
    my_bucket.upload_file('unzipped/{}.csv'.format(uloc[:-4]), 'cleaned_data/{}/{}.csv'.format(year,uloc[:-4]))
    os.remove('unzipped/{}.csv'.format(uloc[:-4]))

