# **M Y    P O R T F O L I O**


### This is my professional Data portfolio. 

On folder [projects](./projects/), you will see:

### **1** - End to End EDA using Python and its Data Analysis Libraries
![Line Chart Viz - One Million](./images/Screenshot%20One%20Million%20Headlines.png)

The first project, named [One Million](./projects/One-Million-08082024.ipynb), although it is a .ipynb file, you can visualize it in this platform. 
If you want to check whether the code is running, so the most efficient tool in this case is Jupyter Notebooks (or Jupyter Labs). 
For that, it's highly recommended to use Anaconda browser, with Jupyter Notebooks/Labs installed. 

### **2** - End to End Business Analysis Dashboard using SQL Server, Data Modelling and Power BI
![Electro Movement ](./images/Screenshot%20Dashboard%20PBI.png)
The second project was made using MS SQL Server and Power BI project and was created for a fictional business called [BikeStoreProject](https://app.powerbi.com/groups/me/reports/442ff52a-57b7-450b-938c-cf1c5b04866b?pbi_source=desktop). The database is spread into three files: [bike_share_yr_0](./miscelaneous/bike_share_yr_0.csv), [bike_share_yr_1](./miscelaneous/bike_share_yr_1.csv) and [cost_table](./miscelaneous/cost_table.csv)  
You can access the dashboard clicking on the link above, if you have access to a Microsoft Fabric / Power BI app, or, alternatively, you can check the [pdf file](./miscelaneous/BikeStoreProject.pdf) uploaded - SQL Query included.
In a nutshell, based on the analysis proceeded, we've recommended an increase of 

### **3** - End to End App Investment Analysis using Briefer, a clould service data tool that uses Python, SQL, Pivot tables and proper visualizations.
![Apple App Store](./images/dash%20board%20briefer.png)
## Scenario Overview

In this scenario, the stakeholder is an app developer aiming to create a successful, marketable app. To achieve this, the developer seeks to understand the most popular app categories, optimal pricing strategies, and how to maximize platform user ratings.

## Workflow Overview

1. **Dataset Acquisition**  
   We sourced appropriate datasets from Kaggle.com to support our analysis.

2. **Data Exploration**  
   We used SQL to become familiar with the data and determine which columns would be primarily used in the analysis. The main objective was to identify opportunities for investment by examining key metrics within the dataset.

3. **Exploratory Data Analysis (EDA)**  
   After a preliminary examination of the data, we began an Exploratory Data Analysis (EDA). This involved data cleaning and verifying compatibility between dataset frames to ensure consistency.

4. **Data Analysis**  
   We executed several queries to uncover insights, including analyses of:
   - The most numerous app genres.
   - User ratings in combination with price ranges and genres.
   - The lowest-rated app genres.
   - Correlations between app description length and average user ratings.
   - Correlations between average ratings and the number of languages provided by the app.
   - Genres that are least common among the lowest-rated categories.
   - The relationship between app price range, number of apps, and average user ratings.

5. **Visualizations**  
   We utilized various dashboard visualizations available on Briefer, such as stacked bar charts, grouped bar charts, and heat maps, some enhanced with labels. Additionally, we employed a Python Bubble chart visualization for a specific insight.

## Recommendations
images/dash board briefer.png
Based on our findings, we crafted several recommendations:

- **Target Underserved Categories**  
  Consider developing an app in underrepresented, low-rated categories such as Catalogs, Finance, and Navigation. These categories present potential opportunities due to their smaller number of apps, which means less competition. A well-designed app with superior user experience could fill existing gaps and capitalize on the lack of strong contenders.

- **Books Category Investigation**  
  For the Books category, further investigation is needed to determine whether the low ratings are due to content quality or the e-reader functionality. Clarifying this could reveal whether this area presents a viable opportunity for development.

- **Pricing Model**  
  We recommend launching a paid app priced between USD 1.00 and USD 4.00 or adopting a freemium model. This model allows attracting a larger initial user base by offering basic features for free while monetizing through premium options.

- **Language Support**  
  Supporting multiple languages could increase the app's reach and appeal in global markets.

