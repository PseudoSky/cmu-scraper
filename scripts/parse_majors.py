#!/usr/bin/env python3
# @file parse_degree.py
# @brief Parses course information from course descriptions pages on
#        http://coursecatalog.web.cmu.edu/ into a JSON file.
#
#        Usage: python parse_descs.py [INFILE] [OUTFILE]
#
#        INFILE: A file containing a list of links of pages to parse.
#        OUTFILE: Where to place resulting JSON.
# @author Justin Gallagher (jrgallag@andrew.cmu.edu)
# @since 2014-12-13

# @brief Parses FCE data for MSXML files downloaded from
#        http://cmu.smartevals.com into a JSON file.
#
#        MSXML is used to compensate for a bug in the FCE export feature: The
#        first few lines of any output are cut off. MSXML is the only format to
#        have enough useless metadata at the beginning of the file to prevent
#        important data from being cutoff.
#
#        Usage: python parse_fces.py [OUTFILE] <USERNAME PASSWORD>
#
#        OUTFILE: Where to place resulting JSON.
#        USERNAME: Andrew username to use to download data.
#        PASSWORD: Andrew password to use to download data.
# @author Justin Gallagher (jrgallag@andrew.cmu.edu)
# @since 2015-01-22

import sys
import json
import bs4
import copy
import cmu_auth
import urllib.parse
import urllib.request
import getpass
import re
import pydash as _


# Constants
USAGE = 'Usage: python parse_fces.py [OUTFILE] <USERNAME PASSWORD>'
LOGIN_URL = 'https://www.smartevals.com/login.aspx?fromschoollist=true&s=cmu'
SOURCE_URL = 'https://enr-apps.as.cmu.edu/audit/audit'
URL_PARAMS = {
  'major':'null',
  'year':'null',
  'college':'CIT'
}


COLLEGES=['CFA','CIT','CMU','DC','HSS','MCS','SCS','TSB']
DEPARTMENTS={'ACCOMP':'ACCOMP','ANTHRO':'ANTHRO','ANTHIS':'ANTHIS','ARC':'ARC','ART':'ART','AUDENGR':'AUDENGR','BSC':'BSC','BIOARC':'BIOARC','BIOART':'BIOART','BIODES':'BIODES','BIODRA':'BIODRA','BIOMUS':'BIOMUS','BSCPSY':'BSCPSY','BSCCB':'BSCCB','BSCNSC':'BSCNSC','BA':'BA','BATECH':'BATECH','BAENT':'BAENT','BAFIN':'BAFIN','BAGENMAN':'BAGENMAN','BAGMM':'BAGMM','BAITM':'BAITM','BAIMN':'BAIMN','BAMARK':'BAMARK','CHE':'CHE','CMY':'CMY','CMYARC':'CMYARC','CMYART':'CMYART','CMYDES':'CMYDES','CMYDRA':'CMYDRA','CMYMUS':'CMYMUS','CHINES':'CHINES','CIV':'CIV','CEE':'CEE','COGSCI':'COGSCI','COLPIA':'COLPIA','COMDES':'COMDES','COMP':'COMP','BSCCBIO':'BSCCBIO','COMPFIN':'COMPFIN','CS':'CS','CSARC':'CSARC','CSDES':'CSDES','CSDRA':'CSDRA','COND':'COND','CW':'CW','DECSCI':'DECSCI','DES':'DES','ECO':'ECO','ECOMTH':'ECOMTH','ECOSTA':'ECOSTA','ECE':'ECE','EPP':'EPP','ENG':'ENG','ENTECH':'ENTECH','ENVENG':'ENVENG','ETHICS':'ETHICS','EHPP':'EHPP','FRENCH':'FRENCH','FRANCO':'FRANCO','GAMEDESG':'GAMEDESG','GERMAN':'GERMAN','GS':'GS','GSM':'GSM','HSSARC':'HSSARC','HSSART':'HSSART','HSSDES':'HSSDES','HSSDRA':'HSSDRA','HSSMUS':'HSSMUS','HIS':'HIS','HISPOL':'HISPOL','MHCI':'HCI','INDDES':'INDDES','IN':'IN','INFOSYS':'INFOSYS','ISSTA':'ISSTA','ISDES':'ISDES','INTDES':'INTDES','INTDES':'INTDES','INTRELP':'INTRELP','JAPAN':'JAPAN','LNGHSS':'LNGHSS','LOGCPTA':'LOGCPTA','ML':'ML','MGLECO':'MGLECO','MSE':'MSE','MSCCAM':'MSCCAM','MSCDML':'MSCDML','MSCM':'MSCM','MSCOR':'MSCOR','MSCSTA':'MSCSTA','MTHECO':'MTHECO','MSCSTAT':'MSCSTAT','MTHARC':'MTHARC','MTHART':'MTHART','MTHDES':'MTHDES','MTHDRA':'MTHDRA','MTHMUS':'MTHMUS','MEG':'MEG','MEDDES':'MEDDES','MLESL':'MLESL','MUSCOM':'MUSCOM','MUSED':'MUSED','MP':'MP','MUSPERF':'MUSPERF','MPORG':'MPORG','MPPIA':'MPPIA','MPVOI':'MPVOI','MUSTECH':'MUSTECH','MUSTHEOR':'MUSTHEOR','NEUROSCI':'NEUROSCI','PPIA':'PPIA','PVOI':'PVOI','PHI':'PHI','PHY':'PHY','PHYARC':'PHYARC','PHYART':'PHYART','PHYDES':'PHYDES','PHYDRA':'PHYDRA','PHYMUS':'PHYMUS','PHYAPP':'PHYAPP','PHYAST':'PHYAST','PHYCHM':'PHYCHM','PHYCP':'PHYCP','POLMGMT':'POLMGMT','POLSCI':'POLSCI','POLPUB':'POLPUB','PW':'PW','PSY':'PSY','PSYBSC':'PSYBSC','ROBSYSDV':'ROBSYSDV','ROB':'ROB','RUSSTU':'RUSSTU','STPP':'STPP','SCICOM':'SCICOM','SH':'SH','SCH':'SCH','SDS':'SDS','SE':'SE','SOUNDDES':'SOUNDDES','SPANISH':'SPANISH','STA':'STA','STAMSC':'STAMSC','STAMSC':'STAMSC','STASN':'STASN','STAMACH':'STAMACH','TW':'TW','TWCM':'TWCM'}

# @function download_catalog_year
# @brief Downloads FCE data from the smartevals website as MSXML.
# @param degree: The smartevals website divides departments into 'degree''s seemingly
#        arbitrarily, each one having a code.
# @param username: Andrew username to use for authentication.
# @param password: Andrew password to use for authentication.
# @param authtoken: Authenication token returned by authenticate.
# @return: Raw text for the MSXML file for this division's FCE data

def download_catalog_year(college_pages, auth):
    # Create target URL
    parameters = copy.copy(URL_PARAMS)
    url = SOURCE_URL + '?' + urllib.parse.urlencode(parameters)
    parameters['changeMajor']='Next'
    parameters['call']='5'

    for college in COLLEGES:
      parameters['college']=college
      print('Downloading College',college)
      for idx,major in enumerate(college_pages[college]):
        print('    Getting Degree', major['name'])
        parameters['major']=major['name']

        url = SOURCE_URL + '?' + urllib.parse.urlencode(parameters)
        export_page=auth.get(url).content
        soup = bs4.BeautifulSoup(export_page)
        # print(export_page)
        data=soup.select('option')
        # print(data)
        if len(data) > 0:
          college_pages[college][idx]['year']=_.map_(soup.select('option'),lambda x: _.strip_tags(x))
        else:
          # print(soup.find('body table tbody'))
          decoded = export_page.decode()
          college_pages[college][idx]['MajorFile']=decoded.split('name=MajorFile value=')[1].split('>')[0]

          year=_.js_match(_.js_match(export_page,'/[<input type=hidden name=year year="](\d{4})/'),'/\d{4}/')
          college_pages[college][idx]['year']=year

        # if idx>5:
        #   return college_pages
        # print(college_pages[college][idx])


    return college_pages




# @function download_degree
# @brief Downloads FCE data from the smartevals website as MSXML.
# @param degree: The smartevals website divides departments into 'degree''s seemingly
#        arbitrarily, each one having a code.
# @param username: Andrew username to use for authentication.
# @param password: Andrew password to use for authentication.
# @param authtoken: Authenication token returned by authenticate.
# @return: Raw text for the MSXML file for this division's FCE data

def download_majors(username, password):
    # Create target URL
    college_pages={}
    parameters = copy.copy(URL_PARAMS)
    url = SOURCE_URL + '?' + urllib.parse.urlencode(parameters)
    parameters['changeCollege']='Next'
    parameters['call']='4'
    # Get viewstate
    s = cmu_auth.authenticate(url, username, password)
    for college in COLLEGES:
      parameters['college']=college
      url = SOURCE_URL + '?' + urllib.parse.urlencode(parameters)

      export_page=s.get(url).content
      soup = bs4.BeautifulSoup(export_page)
      # _.map_(soup.select('option'),lambda x:print(_.strip_tags(x).split(' in ')))
      college_pages[college]=_.chain(soup.select('option')).map(lambda x: _.strip_tags(x)).map(lambda x: {'name':x,'department':x.split(' in ')[1], 'type':x.split(' in ')[0] }).value()


    return {'data':college_pages,'auth':s }



if __name__ == '__main__':
    # Verify arguments
    if not (len(sys.argv) == 4 or len(sys.argv) == 2):
        print(USAGE)
        sys.exit()

    outpath = sys.argv[1]

    if(not(username)):
        if (len(sys.argv) == 2 ):
            print('Please input your Andrew username and password. '
                  'We never store your login info.')
            username = input('Username: ')
            password = getpass.getpass()
        else:
            username = sys.argv[2]
            password = sys.argv[3]

    # Get and write out JSON
    print('Parsing FCEs. This will take a few minutes...')
    data = download_majors(username, password)
    data = download_catalog_year(data['data'],data['auth'])
    print('Writing data...')
    with open(outpath, 'w') as outfile:
        json.dump(data, outfile)

    print('Done!')




# https://enr-apps.as.cmu.edu/audit/audit?call=4&major=BA+in+ARC&year=null&college=CIT&changeCollege=Next


# https://enr-apps.as.cmu.edu/audit/audit?call=4&major=null&year=null&college=CFA&changeCollege=Next
# call:4
# major:null
# year:null
# college:CFA
# changeCollege:Next


# <HEAD><TITLE>S3 Academic Audit On-Line</TITLE></HEAD>
# <body bgcolor=#669999>
# <form action=audit method=GET target=body>
# <table border=0 width=650>
# <tr>
# <td>&nbsp;<img src=/audit/web/images/mast_text.gif width=294 height=26 alt=mast_text.gif (1984 bytes)></td>
# <td align=right>
# <input type=submit name=call value=Help>
# <input type=submit name=call value=Advisor>
# <input type=submit name=call value=Feedback>
# <a href=audit target=_parent>Start Over</a>
# </td></tr></table></form>
# <table width=650 align=left border=0 cellspacing=0 cellpadding=2>
# <tr align=CENTER>
# <td align=center width=216><div align=center><center>
# <form action=audit method=GET target=head>
# <input type=hidden name=call value=4>
# <input type=hidden name=major value="null">
# <input type=hidden name=year value="null">
# <table nowrap width=200 allign=center cellpadding=2 cellspacing=0 border=0>
#   <tr bgcolor=#808000>
#      <td align=center>
#       <small><strong>
#       <font face=Arial>Select <a href=audit?call=13 target=body>College</A></font>
#     </strong></small>
#     </td>
#   </tr>
#    <tr bgcolor=#FFFFCC>
# <td><center><small><b><font face=Arial>CFA</font></b></small></center></td>
#   </tr>
# </table></form>
# </center></div></td>
# <td align=center width=216><div align=center><center>
# <form action=audit method=GET target=head>
# <input type=hidden name=call value=5>
# <input type=hidden name=college value="CFA">
# <input type=hidden name=year value="null">
# <table width=200 allign=center cellpadding=2 cellspacing=0 border=0>
#   <tr bgcolor=#808000>
#     <td align=center colspan=3>
#       <small><strong>
#       <font face=Arial>Select <a href=audit?call=12 target=body>Major</a></font>
#     </strong></small>
#     </td>
#   </tr>
#    <tr nowrap bgcolor=#FFFFCC>
#     <td align=center >
#       <div align=center><center><p>
#         <input type=Submit name=changeMajor value=Prev>
#     </td>
#       <td align=center>
#         <div align=center><center><p>
#       <select name=major size=1>
#         <option>BA in ARC</option>
#         <option>BAC in ARC</option>
#         <option>BDES in DES</option>
#         <option>BFA in ART</option>
#         <option>BFA in COMDES</option>
#         <option>BFA in DES</option>
#         <option>BFA in INDDES</option>
#         <option>BFA in MP</option>
#         <option>BFA in MPORG</option>
#         <option>BFA in MPPIA</option>
#         <option>BFA in MPVOI</option>
#         <option>BFA in MUSCOM</option>
#         <option>MDES in CPID</option>
#         <option>MDES in INTDES</option>
#         <option>MINOR in ACCOMP</option>
#         <option>MINOR in ARC</option>
#         <option>MINOR in ART</option>
#         <option>MINOR in COMDES</option>
#         <option>MINOR in DES</option>
#         <option>MINOR in INDDES</option>
#         <option>MINOR in JAZZP</option>
#         <option>MINOR in MEDDES</option>
#         <option>MINOR in MUSC</option>
#         <option>MINOR in MUSCOND</option>
#         <option>MINOR in MUSCTECH</option>
#         <option>MINOR in MUSCTHRY</option>
#         <option>MINOR in MUSED</option>
#         <option>MINOR in MUSPERF</option>
#         <option>MINOR in MUSTECH</option>
#         <option>MINOR in MUSTHEOR</option>
#         <option>MINOR in SOUNDDES</option>
#         <option>MMU in COLPIA</option>
#         <option>MMU in COMP</option>
#         <option>MMU in COND</option>
#         <option>MMU in P</option>
#         <option>MMU in PPIA</option>
#         <option>MMU in PVOI</option>
#         <option>PHD in DES</option>
#           </select>
#     </td>
#     <td align=center><input type=Submit name=changeMajor value=Next></td>
#   </tr>
# </table></form>
# </center></div></td>
# <td align=center width=216><div align=center><center>
# <form action=audit method=GET target=head>
# <input type=hidden name=call value=6>
# <input type=hidden name=college value="CFA">
# <input type=hidden name=major value="null in null">
# <table nowrap width=200 allign=center cellpadding=2 cellspacing=0 border=0>
#   <tr bgcolor=#808000>
#      <td align=center>
#       <small><strong>
#       <font face=Arial>Select Catalog Year</font>
#     </strong></small>
#     </td>
#   </tr>
#    <tr bgcolor=#FFFFCC>
# <td><small><center><b><font face=Arial>---</font></b></small></center></td>
#   </tr>
# </table></form>
# </center></div></td>
# </tr></table>
# </body>
