# debug here in terminal, then upload these files to notebook here http://34.121.204.181:5000/tree/GCP%20Code#, go to terminal within notebook and run 'gcloud app deploy' (same as debug)
# use "jupyer-notebook --no-browser --port=5000" to open notebook from VM instance in GCP
# use 'gcloud app deploy' to deploy to website. must run in the 'GCP Code' directory
# use 'python main.py' where main.py is the file of this scrript
# always use 'python3 -m pip install' instead of 'pip install' because it upgrades the correct version of python. https://snarky.ca/why-you-should-use-python-m-pip/
# Service account name is janovsky_analytics


#flask provides framework for website
from flask import Flask, render_template, url_for, request, redirect
#need urlopen to access nba stats from url
import ssl
from urllib.request import urlopen
#need beautifulsoup to webscrape nba stats
from bs4 import BeautifulSoup
#need series for appending to dataframe, need dataframe to hold nba stats data
from pandas import DataFrame, Series
#need logging to document step-by-step events for troubleshooting
import logging
#need bigquery to pull data from GCP databasr (BigQuery)
from google.cloud import bigquery

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def homepage():
    # create logger for step-by-step events
    # logging.basicConfig(filename='website_log_v2.log', format='%(asctime)s %(message)s', filemode='w')
    # log = logging.getLogger("my logger")
    # log.setLevel(logging.DEBUG)

    # write first log
    # log.info("Application started")

    # open GCP BigQuery connection to pull data from database
    bqclient = bigquery.Client()
    # log.info("BigQuery Client created")

    # query to get the 5 most recent web scrape dates, these will be used in the dropdown
    bq_cr_ts = """
        select left(cr_ts, 5)
        from `nba-stats-website-317623.nba_stats.nba_stats_table_3`
        group by cr_ts
        order by cr_ts desc
        limit 5
    """

    # pull the data from BigQuery database using the string above, and put the results into a dataframe
    cr_ts_df = bqclient.query(bq_cr_ts).result().to_dataframe(create_bqstorage_client=True)

    # convert the dataframe to a list so they can looped through and edited
    cr_ts_list = cr_ts_df.values.tolist()

    # create empty list that the edited data can be appended to
    cr_ts_list_new = []

    # loop through all the cr_ts, remove the brackets and quotes, then append to the empty list. These date strings will be used when pulling data from BigQuery database
    for cr in cr_ts_list:
        cr_ts_str = str(cr).replace('[\'','').replace('\']','')
        cr_ts_list_new.append(cr_ts_str)

    # set the most recent date as the default value (to use when pulling data from BigQuery) when loading the web page
    cr_ts_sql = cr_ts_list_new[0]

    # change the dataset if user changes drop down
    if request.method == "POST":
        cr_ts_sql = request.form.get('dynamic_cr_ts')

    # query for pulling nba stats from BigQuery for the given cr_ts (web scrape date)
    query_string_stg = """
        SELECT distinct player
            , team
            , mp
            , pts
            , ast
            , trb
            , perc_fg
            , perc_3p
            , perc_ft
            , cr_ts
        FROM    `nba-stats-website-317623.nba_stats.nba_stats_table_3`  
        where  left(cr_ts, 5) = 'insert_date'
        and team = 'DAL'
        order by team, player desc
    """

    # edit the query to contain the given cr_ts. this can be the default (cr_ts_list_new[0]) or it can be user selected (request.form.get('dynamic_cr_ts')
    query_string = query_string_stg.replace('insert_date',cr_ts_sql)

    # pull nba stats from BigQuery and convert to a dataframe
    nba_data_df = bqclient.query(query_string).result().to_dataframe(create_bqstorage_client=True)
    
    #sort by most points per game
    nba_data_df['PTS_float'] = nba_data_df['pts'].astype(float)
    nba_data_df = nba_data_df.sort_values(by='PTS_float', ascending=False)
    nba_data_df = nba_data_df[['player', 'team', 'mp', 'pts', 'ast', 'trb', 'perc_fg', 'perc_3p', 'perc_ft', 'cr_ts']]

    #convert data to a list of lists so we can pass that to the HTML to loop through
    nba_data_list = nba_data_df.values.tolist()

    # log.info("Dataframe is about to be sent to HTML")
    return render_template('page.html', data=nba_data_list, dynamic_dt=cr_ts_list_new)
    # return render_template('page2.html', tables=[nba_data.to_html(classes='data', header="true")])




@app.route("/test", methods=['GET', 'POST'])
def test():
    #create logger for step-by-step events
    # logging.basicConfig(filename='website_log_v2.log', format='%(asctime)s %(message)s', filemode='w')
    # log = logging.getLogger("my logger")
    # log.setLevel(logging.DEBUG)

    # #write first log
    # log.info("Application started")

    #web scrape nba data and return dataframe with stats
    # nba_data = pull_nba_data()
    # nba_data = pull_bigquery_data()

    bqclient = bigquery.Client()

    query_string = """
        SELECT *
        FROM    `nba-stats-website-317623.nba_stats.nba_stats_table_5` 
        where  cr_ts = '2021-09-12' 
        limit 10  
    """
    nba_data = bqclient.query(query_string).result().to_dataframe(create_bqstorage_client=True)

    query_string2 = """
        SELECT *
        FROM    `nba-stats-website-317623.nba_stats.nba_stats_table_5` 
        where  cr_ts = '2021-09-12' 
        limit 100  
    """
    nba_data2 = bqclient.query(query_string2).result().to_dataframe(create_bqstorage_client=True)
    
    #sort by most points per game
    nba_data['PTS_float'] = nba_data['pts'].astype(float)
    nba_data = nba_data.sort_values(by='PTS_float', ascending=False)
    nba_data = nba_data[['player', 'team', 'mp', 'pts', 'ast', 'trb', 'perc_fg', 'perc_3p', 'perc_ft']]

    #convert data to a list of lists so we can pass that to the HTML to loop through
    nba_data = nba_data.values.tolist()
    
    return render_template('page.html', data=nba_data)



# def pull_nba_data():
#     # log = logging.getLogger("my logger")
#     # log.info("Inside pull_nba_data function")

#     #needed for urlopen: https://stackoverflow.com/questions/35569042/ssl-certificate-verify-failed-with-python3
#     ssl._create_default_https_context = ssl._create_unverified_context

#     #open url containing nba stats data and get the html used in the webpage
#     per_36_min_html = urlopen('https://www.basketball-reference.com/playoffs/NBA_2021_per_game.html')
#     # log.info("URL is opened")

#     #parse html from webpage using beautifulsoup
#     per_36_min_soup = BeautifulSoup(per_36_min_html)

#     #the table rows are identified by 'tr' - the first row includes the column names
#     #within each row, we can identify the columns with the 'th' element
#     col_names = []

#     soup_stats = per_36_min_soup.findAll('tr')[0]

#     #create a list (col_names_soup) of html which includes the column names, then loop through the list and 
#     #add the column name texts to a list (col_names). skip the rank since its not needed
#     col_names_soup = soup_stats.findAll('th')
#     for col in range(1, len(col_names_soup)):
#         col_names.append(col_names_soup[col].getText())
#         #print(str(col) + '. ' + col_names_soup[col].getText())

#     #create empty dataframe using column names pulled earlier
#     nba_stats = DataFrame(columns = col_names)
#     # log.info("Dataframe of " + str(len(col_names)) + " column names has been created")

#     #get all rows of players (except column header)
#     rows_of_players = per_36_min_soup.findAll('tr')[1:]

#     #loop through each row of players
#     for row in range(0, len(rows_of_players)):
#         #need to remove rows with just column headers
#         if str(rows_of_players[row]['class'][0]) != 'thead':
#             columns = rows_of_players[row].findAll('td')
#             player_stats = []
#             #go through each column of player stats and add each stat to the list (player_stats) for a given player 
#             for col in range(0, 29):
#                 player_stats.append(columns[col].getText())
#             #convert list to a pandas series so it can be appeneded to dataframe
#             player_stats_append = Series(player_stats, index=col_names)
#             #append player stats to nba stats dataframe
#             nba_stats = nba_stats.append(player_stats_append, ignore_index=True)
#     # log.info("Dataframe has been loaded with " + str(nba_stats.shape[0]) + " rows")
    
#     #only look at first 5 rows
#     nba_stats_reduce = nba_stats[['Player', 'Tm', 'MP', 'PTS', 'AST', 'TRB', 'FG%', '3P%', 'FT%']]

#     #sort by most points per game
#     nba_stats_reduce['PTS_float'] = nba_stats_reduce['PTS'].astype(float)
#     nba_stats_reduce = nba_stats_reduce.sort_values(by='PTS_float', ascending=False)
#     nba_stats_reduce = nba_stats_reduce[['Player', 'Tm', 'MP', 'PTS', 'AST', 'TRB', 'FG%', '3P%', 'FT%']]
    
#     #return dataframe of stats
#     # log.info("pull_nba_data is about to return a dataframe with " + str(nba_stats_reduce.shape[0]) + " rows and " + str(nba_stats_reduce.shape[1]) + " columns")
#     return nba_stats_reduce


 
if __name__ == "__main__":
    app.run(debug=True)


