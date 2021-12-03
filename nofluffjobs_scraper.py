from bs4 import BeautifulSoup
from time import sleep
import re
import xlsxwriter
import requests

# link to search without page number
# maybe should get it as args for script
global Link
Link = 'https://nofluffjobs.com/jobs/frontend?page='

# count of each technology that required
global skillStats
skillStats = dict()


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
    # Parse content by tag 'a' and id that contains 'nfjPostingListItem-' - it is job offers
    soup = BeautifulSoup(page.content,'html.parser')
    results = soup.find_all('a',id = re.compile('^nfjPostingListItem-'))
    # Return finded offers 
    return(results)

# Get specified offer info(required skills)
def getOfferInfo(URL):
    # Get page content
    while (True):
        try:
            page = requests.get(URL)
            break
        except:
            print("Error while getting page content. Will wait 2 second and try again")
            sleep(5)
    soup = BeautifulSoup(page.content,'html.parser')
    skills = []
    # Parse content of requirements block
    # Get first buttons from 'must have' and 'nice to have' - they have different declaration
    results1 = soup.find_all('a',class_='btn btn-outline-success btn-sm text-truncate')
    for result in results1:
        skills.append((result.get_text()).lower())

    # Get another skills
    results2 = soup.find_all('button',class_='btn btn-outline-success btn-sm no-cursor text-truncate')
    for result in results2:
        skills.append((result.get_text()).lower())

    # Return skills set
    return(skills)

# Counts each skill in all offers
def calculateSkillsStats(skill):
    if (skill in skillStats):
        skillStats[skill] += 1
    else:
        skillStats[skill] = 1

# Create xlsx file, worksheet and fill out header
def initializeTable():
    # Create an new Excel file 
    workbook = xlsxwriter.Workbook('jobs.xlsx')

    # Add worksheet
    offersWorksheet = workbook.add_worksheet('Jobs')
    statsWorksheet = workbook.add_worksheet('Statistic')

    # Add chart
    chart = workbook.add_chart({'type':'pie'})

    # Write headers to offers page
    offersWorksheet.write(0, 0, 'Title')
    offersWorksheet.write(0, 1, 'Salary Start')
    offersWorksheet.write(0, 2, 'Salary End')
    offersWorksheet.write(0, 3, 'Location')
    offersWorksheet.write(0, 4, 'Link')
    offersWorksheet.write(0, 5, 'Skills->')
    # Write headers to stats page
    statsWorksheet.write(0, 0, 'Skill')
    statsWorksheet.write(0, 1, 'Count')
    return(workbook,offersWorksheet,statsWorksheet,chart)

# Write job offers to worksheet, starting from specified row
def writeOffersToTable(worksheet,results,start):
    # Iterate through results(job), parse specific data and write to file
    for i,job in enumerate(results,start = start):
    # Find and write job title to column 0
        worksheet.write(i, 0, (job.find('h3', class_ = 'posting-title__position color-main ng-star-inserted')).get_text())
    # Find salary range and conver it to 'start' and 'end' values, if its strict - write value at both cells(1 and 2 columns)
        try:
            varSalary =  (job.find('span', class_ = 'text-truncate badgy salary btn btn-outline-secondary btn-sm ng-star-inserted')).get_text()
        except:
            varSalary = '0'
        if ('-' in varSalary):
            worksheet.write(i, 1, varSalary[:varSalary.index('-')])
            worksheet.write(i, 2, varSalary[varSalary.index('-')+1:varSalary.index('P')])
        else:
            worksheet.write(i, 1, varSalary[:varSalary.index('P')])
            worksheet.write(i, 2, varSalary[:varSalary.index('P')])
    # Find and write job location to column 3 
        worksheet.write(i, 3, (job.find('span', class_= 'posting-info__location d-flex align-items-center ml-auto')).get_text())
    # Find and write link of a job to column 4
        offerLink = 'https://nofluffjobs.com'+job.get('href')
        worksheet.write(i, 4, offerLink)
    # Get skill from offers page and write them on row
        skills = getOfferInfo(offerLink)
        for j,skill in enumerate(skills,start = 5):
            worksheet.write(i, j, skill)
    # While iteratin through skills lets gather statistic
        calculateSkillsStats(skill)
    # Returning last row so we can start from end next time
    return(i)

def writeStatistic(worksheet,skillStats,chart):
    # Write counts of each skill
    for i,skill in enumerate(skillStats, start = 1):
        worksheet.write(i, 0, skill)
        worksheet.write(i, 1, skillStats[skill])

    # Create chart
    # Last cell
    x = len(skillStats)

    # Determine range for cells (value and label)
    addrValue = '=Sheet2!$B$2:$B$'+str(x)
    addrCat = '=Sheet2!$A$2:$A$'+str(x)

    # Make chart
    chart.add_series({
        'name': 'Skills required', #chart name
        'categories': addrCat, #addresses of labels
        'values': addrValue, #addresses of values
        'data_labels': {'percentage': True,'value': True,'position': 'outside_end','category':True}, #make visible labels,percentages of values and set position
     })
    # Insert chart
    worksheet.insert_chart('C1',chart)

workbook,offersWorksheet,statsWorksheet,chart = initializeTable() #create xlsx file and store workbook and worksheet objects
i = 1 # page iterator
start = 1 # table row iterator

# Endless loop, if we get page without jobs we break from it. Otherwise we write our job into table
while (True):
    results = getPageOffers(i)
    if (len(results) == 0):
        break
    print("Got",i,"pages. Still going, please wait!")
    i+=1
    start=writeOffersToTable(offersWorksheet,results,start)+1 #write to file and store last row index, so we can start from that row next iteration

# Write statistic to other page. Pass sorted dict with skill:count by desc
skillStats = dict(sorted(skillStats.items(), key = lambda x: x[1], reverse = True))
writeStatistic(statsWorksheet,skillStats,chart)

workbook.close() #close our workbook in xlsx file
print("Done")
exit(0)
