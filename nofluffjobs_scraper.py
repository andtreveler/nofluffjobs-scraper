from bs4 import BeautifulSoup
from time import sleep
import re
import xlsxwriter
import requests

#need to OOP?

# link to search without page number
# maybe should get it as args for script
global Link
Link = 'https://nofluffjobs.com/jobs/remote?criteria=seniority%3Djunior&page='



# Get specific page content and parse it with BeautifulSoup
def getPageOffers(pageNumber):
# Get page content
    URL = Link + str(pageNumber)
    while (True):
        try:
            page = requests.get(URL)
            break
        except:
            print("Error while getting page content. Will wait 2 second and try again")
            sleep(5)
# Parse content by tag 'a' and id that contains 'nfjPostingListItem-'
    soup = BeautifulSoup(page.content,'html.parser')
    results = soup.find_all('a',id = re.compile('^nfjPostingListItem-'))
# Return finded offers 
    return(results)

# Create xlsx file, worksheet and fill out header
def initializeTable():
# Create an new Excel file 
    workbook = xlsxwriter.Workbook('jobs.xlsx')
# Add worksheet
    worksheet = workbook.add_worksheet()
# Write headers
    worksheet.write(0, 0, 'Title')
    worksheet.write(0, 1, 'Salary Start')
    worksheet.write(0, 2, 'Salary End')
    worksheet.write(0, 3, 'Location')
    worksheet.write(0, 4, 'Link')
    return(workbook,worksheet)

# Write job offers to worksheet, starting from specified row
def writeToTable(worksheet,results,start):
# Iterate through results(job), parse specific data and write to file
    for i,job in enumerate(results,start = start):
# Find and write job title to column 0
        worksheet.write(i, 0, (job.find('h3', class_ = 'posting-title__position color-main ng-star-inserted')).get_text())
# Find salary range and conver it to 'start' and 'end' values, if its strict - write value at both cells(1 and 2 columns)
        varSalary =  (job.find('span', class_ = 'text-truncate badgy salary btn btn-outline-secondary btn-sm ng-star-inserted')).get_text()
        if ('-' in varSalary):
            worksheet.write(i, 1, varSalary[:varSalary.index('-')])
            worksheet.write(i, 2, varSalary[varSalary.index('-')+1:varSalary.index('P')])
        else:
            worksheet.write(i, 1, varSalary[:varSalary.index('P')])
            worksheet.write(i, 2, varSalary[:varSalary.index('P')])
# Find and write job location to column 3 
        worksheet.write(i, 3, (job.find('span', class_= 'posting-info__location d-flex align-items-center ml-auto')).get_text())
# Find and write link of a job to column 4
        worksheet.write(i, 4, 'https://nofluffjobs.com'+job.get('href'))
# Returning last row so we can start from end next time
    return(i)



workbook,worksheet = initializeTable() #create xlsx file and store workbook and worksheet objects
i = 1 # page iterator
start = 1 # table row iterator

# Endless loop, if we get page without jobs we break from it
while (True):
    results = getPageOffers(i)
    if (len(results) == 0):
        break
    print("Got",i,"pages. Still going, please wait!")
    i+=1
    start=writeToTable(worksheet,results,start)+1 #write to file and store last row index, so we can start from that row next iteration

workbook.close() #close our workbook in xlsx file
exit(0)
