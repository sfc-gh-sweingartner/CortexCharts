# Improved Charts for Cortex Analyst

##This Streamlit in Snowflake app allows you to ask questions to Semantic Models in Snowflake.  You will receive nice looking charts and can assemble them into dashboards

### App Description & Usage
This solution is an uplift to the out of the box exmample Cortex Analyst Streamlit in Snowflake chatbot as found here:  https://quickstarts.snowflake.com/guide/getting_started_with_cortex_analyst/index.html?index=..%2F..index#0   The largest flaw of that solution is that when you ask a question, you get data in a table fine but the charts rarely work well.   

With this solution, there are 9 preconfigured chart templates and the correct one will automatically return based on how many date, text, and numeric columns exist in the dataset that was returned.  The logic for which chart applies is as follows.  
![Chart Number Logic](/images/4.png)

Your first interaction with this application is quite similar to the Quickstart.  You ask a question and get a response.  What you will find is that the charts are better.  
![Cortex Analyst Page](/images/2.png)

If you like the chart that's returned and want to be able to run it again without calling Cortex Analyst, then click the button "Open in Designer"

A few minor changes to this Cortex Analyst page are: 
1) Semantic model warnings have been commented out
2) The generic question of "What sort of questions can I ask" no longer runs automatically
3) There is now a button to enable SQL to return without auto running it

![Cortex Analyst Page](/images/1.png)
Clicking the button on the Cortex Analyst Page opens up the same SQL Statement, table, and chart in the Report Designer page.  
On this page, you can:
1) Make minor changes to the SQL
2) Make changes to the Altair chart code to further improve the chart.  (e.g. change the color, size of bubbles, chart name, etc...)   See the Altair project for guidance on what you can do.
3) Provide a custom name to the report
4) Override the prompt interpretation if you want to type your own description
5) Save the report into a CORTEX_ANALYST_REPORTS table

Then use the navigaion menu on the left to open the Dashboard page
![Cortex Analyst Page](/images/6.png)
Your first task is to name your first dashboard.  You can create many dashboards.  These dasboards are saved into the CORTEX_ANALYST_DASHBOARDS table
In the table at the bottom is a list of every report saved.  Tick the box for the reports you want assembled onto this dasboard and click "Save Dashboard" 

### How to Deploy (Alternatively download the files if you don't want to connect to Git) 
1) In Snowsight, open a SQL worksheet and run this with ACCOUNTADMIN to allow your env to see this GIT project:
    CREATE OR REPLACE API INTEGRATION git_sweingartner
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-sweingartner')
    ENABLED = TRUE;
3) click Projects > Streamlit
4) Tick the drop downbox next to the blue "+ Streamlit App" and select "create from repository"
5) Click "Create Git Repository"
6) In the Repository URL field, enter: https://github.com/sfc-gh-sweingartner/CortexCharts
7) In the API Integration drop down box, choose GIT_SWEINGARTNER
8) Deploy it into any DB, Schema and use any WH
9) Click Home.py then "Select File"
10) Click create
11) Open the code editor panel and edit which yaml file (i.e. semantic model) that the solution is looking at.  You will find the line to alter at line 39 of the 1_Cortex_Analyst.py file

Run the App.  

Note that if you want to demo against the Synthea healthcare Dataset, refer to this Git and request a datashare: https://github.com/sfc-gh-sweingartner/synthea/tree/main

Reach out to stephen.weingartner@snowflake.com with any issues.  

### Version History
V1. 25 - Apr - Initial release
V2. All the python scripts were modified to support one more chart (i.e. 10 which supports KPI's) This appears when there is one row of data to show up to four KPI's for up to four numeric columns.  Also fixed Chart 9 which was always a single color.  Now the user can select both the x axis and also the color for the stacked bar stripes.  
