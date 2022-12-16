#!/usr/bin/env python
# coding: utf-8

# In[6]:


import xmltodict
import os
import pandas as pd
import time
import boto3
import shutil
from nltk.corpus import stopwords
from collections import Counter
import re
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
import nltk
nltk.download('averaged_perceptron_tagger')
from nltk.corpus import wordnet


# In[7]:


stop = stopwords.words('english')
lemmatizer = WordNetLemmatizer()
porter = PorterStemmer()


# In[8]:


# POS_TAGGER_FUNCTION : TYPE 1
def pos_tagger(nltk_tag):
    #print("Tag is here ",nltk_tag)
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:         
        return None


# In[9]:


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
    word_counts = []
    
    files = os.listdir('Unzipped/{}'.format(partition))
    for file in files: 
        word_list = []
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
                
                for i in range(len(dic['us-patent-application']['claims']['claim'])):
                    try:
                        text = dic['us-patent-application']['claims']['claim'][i]['claim-text']['#text']
                        
                        all_words = re.sub(r'[^\w\s]', '', text).split()

                        pos_tagged = nltk.pos_tag(all_words) 
                        
                        wordnet_tagged = list(map(lambda x: (x[0], pos_tagger(x[1])), pos_tagged))
                        
                        
                        lemmatized_sentence = []
                        for word, tag in wordnet_tagged:
                            if tag is None:
                                # if there is no available tag, append the token as is
                                lemmatized_sentence.append(word)
                            else:       
                                # else use the tag to lemmatize the token
                                lemmatized_sentence.append(lemmatizer.lemmatize(word, tag))
                        
                        filtered_words = [word.lower() for word in lemmatized_sentence if word.lower() not in stop]
                        word_list.extend(filtered_words)
                    except:
                        continue
                word_counts.append(Counter(word_list).items())
            except:
                continue
                
    df = pd.DataFrame(list(zip(doc_numbers, titles, utilities, dates, countries, org_names, org_cities, org_countries, nois, abstracts, word_counts)),
               columns =['Doc_number', 'Title', 'Type','App_Date','Country','Org_Name','Org_City','Org_Country','No_inventors','Abstract','Description'])
    
    df['App_Date'] = pd.to_datetime(df['App_Date'])
    
    
    return df


# In[10]:


access_key_id  = ''
secret_access_key = ''

session = boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
resources = session.resource('s3')

s3 = session.client('s3')
my_bucket = resources.Bucket('capstone-storage')


# In[11]:


response = s3.list_objects_v2(Bucket='capstone-storage')
files = response.get("Contents")


# In[12]:


locs = []

for file in files:
    if file['Key'].endswith('.zip'):
        locs.append(file['Key'])


# In[13]:


updated_locs = []
for loc in locs:
    file_name = loc.split('/')[2]
    if len(file_name.split('_'))>1 and file_name.endswith('.zip'):
        updated_locs.append(file_name.split('_')[0]+'.zip')
    elif file_name.endswith('.zip'):
        updated_locs.append(file_name)
    else:
        continue


# In[ ]:


for loc,uloc in zip(locs,updated_locs):
    year = loc.split('/')[1]
    if int(year)!=2019:
        continue
    out_file = loc.split('/')[2] #has zip tag
    s3.download_file('capstone-storage',loc,Filename='unzipped/'+out_file)
    os.system('unzip unzipped/{} -d unzipped'.format(out_file))
    os.system('python3 parse_patents.py -i Unzipped/{}.xml'.format(uloc[:-4]))
    os.remove('unzipped/{}.xml'.format(uloc[:-4]))
    os.remove('unzipped/{}'.format(out_file))
    df = dataframe_generator(uloc[:-4])
    shutil.rmtree('Unzipped/{}'.format(uloc[:-4]))
    df.to_csv('unzipped/{}.csv'.format(uloc[:-4]))
    my_bucket.upload_file('unzipped/{}.csv'.format(uloc[:-4]), 'cleaned_data_with_description/{}/{}.csv'.format(year,uloc[:-4]))
    os.remove('unzipped/{}.csv'.format(uloc[:-4]))


# In[ ]:





# In[ ]:




