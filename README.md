# Capstone-Project-2022

 Description:
The goal of our capstone project is to study the impact of COVID-19 on the nature of technological innovation using Google Patent’s text and location data using NLP techniques

Project Guide:
Dr. Jorge Guzman (https://www8.gsb.columbia.edu/cbs-directory/detail/jag2367)

Contributors:
- Shreya Verma
- Malaika Gupta
- Sanjeev Tewani
- Arunit Maity
- Mehrab Singh Gill
- Sarthak Bhargava
  
Brief Description of files and scripts-

Within the scripts folder we have the following code files that deal with the data collection processes and visualizations-

1) Scraping Patent Data.ipynb - Using Selenium, we download the zip files from - https://bulkdata.uspto.gov/data/patent/grant/redbook/fulltext/
2) parse_patents.py - Here, we split a large XML file containing patents for an entire week into individual components
3) XML parsing.py - This code then extracts all relevant information from each patent file and uploads it to an S3 bucket as a csv.
4) Merge-US-data.ipynb - We filter by location to get the US patents and obtain a yearly record of patent applications for 2018-2022
5) LSA_implementation_using_Gensim_with_Coherence_score_plots.ipynb - This contains code for our LDA model's hyperparameter tuning using coherence plots
6) LDA_implementation_tuning.ipynb - This code file then uses the parameters obtained above to complete the optimum topic modeling 
7) plots.py - Here, we conduct some exploratory data analysis and examine the final yearly data in three different ways

With the parent directory, we also have several html files to visualize the topics generated for each year using LDA. They are interactive as well. Additionally, to measure the degree of change in the distribution of topics before and after covid, we conducted significance testing. The code for the same is included in significance_testing.py. The t-SNE subdirectory contains code to visualize our high dimensional data topics for each year.  

