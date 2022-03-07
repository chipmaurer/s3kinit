#!/usr/bin/python

# s3kinitp3.py - authenticate to Identity Provider, receive possible roles, and then select and assume a valid role
# 
# Set the 
# idpentryurl - The URL used by the ADFS Identity Provider associated with the ECS cluster
# iamprovider - The hostname or IP address of the ECS cluster, or a load balancer that can direct 

# This software is distributed 'as is' and with no warranties of any kind, whether express or implied, including and without limitation,
# any warranty of merchantability or fitness for a particular purpose.

# The user (you) must assume the entire risk of using the software.

# In no event shall any individual, company or organization involved in any way in the development, 
# sale or distribution of this software be liable for any damages whatsoever relating to the use, 
# misuse, or inability to use this software (including, without limitation, damages for loss of profits, 
# business interruption, loss of information, or any other loss).'
 
import sys
import boto.sts
import boto.s3
import requests
import getpass
import configparser
import base64
import logging
import xml.etree.ElementTree as ET
import re
import getopt
from bs4 import BeautifulSoup
from os.path import expanduser
from urllib.parse import urlparse, urlunparse
import json

# duration seconds is how many seconds we want the creds for.  Initialize to 1 hr, and change if user passes -H <HR> on command line
duration_seconds = 3600

def parse_args(argv):
    global duration_seconds
    try:
        opts, args = getopt.getopt(argv,"hH:")
    except getopt.GetoptError:
        print ('s3kinitp3.py [-H HOURS]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('s3kinitp3.py [-H HOURS]')
            sys.exit()
        elif opt == '-H':
            if (int(arg) > 12):
                print('Cannot specify credentials to last for more than 12 hours (AWS limit)')
                sys.exit(2)

            duration_seconds = int(arg) * 60 * 60

if __name__ == '__main__':
    
    ##########################################################################
    # Variables
    
    # output format: The AWS CLI output format that will be configured in the
    # saml profile (affects subsequent CLI calls)
    outputformat = 'json'
    
    # SSL certificate verification: Whether or not strict certificate
    # verification is done, False should only be used for dev/test
    sslverification = False
    
    # idpentryurl: The initial url that starts the authentication process.
    idpentryurl = 'https://ad.hdfs.emc.com/adfs/ls/idpinitiatedsignon.aspx?LoginToRp=urn:ecs:7bc786ea-11ee-4b1e-867b-2d05faa8fe54:webservices'
    
    # iamprovider: The IP of the IAM service provider (e.g. ECS)
    iamprovider = '10.247.179.112'
    
    # Uncomment to enable low level debugging
    #logging.basicConfig(level=logging.DEBUG)

    ##########################################################################
    # See if any args were passed
    parse_args(sys.argv[1:])

    # Get the federated credentials from the user
    print("Username@Domain: ", end=' ')
    username = input()
    password = getpass.getpass()
    print('')
    
    # Get the federated credentials from the user
    # print "idpentryurl:",
    # idpentryurl = raw_input()
    # print ''
    
    # Initiate session handler
    session = requests.Session()
    
    # Programmatically get the SAML assertion
    # Opens the initial IdP url and follows all of the HTTP302 redirects, and
    # gets the resulting login page
    formresponse = session.get(idpentryurl, verify=sslverification)
    # Capture the idpauthformsubmiturl, which is the final url after all the 302s
    idpauthformsubmiturl = formresponse.url
    
    # Parse the response and extract all the necessary values
    # in order to build a dictionary of all of the form values the IdP expects
    # print ('************************************************************************************')
    # print (formresponse.text.decode ('utf8'))
    # print ('************************************************************************************')
    formsoup = BeautifulSoup(formresponse.text, features="lxml")
    payload = {}
    
    for inputtag in formsoup.find_all(re.compile('(INPUT|input)')):
        name = inputtag.get('name','')
        value = inputtag.get('value','')
        if "user" in name.lower():
            #Make an educated guess that this is the right field for the username
            payload[name] = username
        elif "email" in name.lower():
            #Some IdPs also label the username field as 'email'
            payload[name] = username
        elif "pass" in name.lower():
            #Make an educated guess that this is the right field for the password
            payload[name] = password
        else:
            #Simply populate the parameter with the existing value (picks up hidden fields in the login form)
            if "formsauthent" in name.lower():
                if value != None and value != "":
                    payload[name] = value
            else:
                payload[name] = value
    # print ('************************************************************************************')
    # Debug the parameter payload if needed
    # Use with caution since this will print sensitive output to the screen
    # print payload
    # print ('************************************************************************************')
    
    # Some IdPs don't explicitly set a form action, but if one is set we should
    # build the idpauthformsubmiturl by combining the scheme and hostname 
    # from the entry url with the form action target
    # If the action tag doesn't exist, we just stick with the 
    # idpauthformsubmiturl above
    for inputtag in formsoup.find_all(re.compile('(FORM|form)')):
        action = inputtag.get('action')
        loginid = inputtag.get('id')
        if (action and loginid == "loginForm"):
            parsedurl = urlparse(idpentryurl)
            idpauthformsubmiturl = parsedurl.scheme + "://" + parsedurl.netloc + action
    
    # Performs the submission of the IdP login form with the above post data
    response = session.post(
        idpauthformsubmiturl, data=payload, verify=sslverification)
    
    # Debug the response if needed
    # print (response.text)
    # print ('************************************************************************************')
    
    # Overwrite and delete the credential variables, just for safety
    username = '##############################################'
    password = '##############################################'
    del username
    del password
    
    # Decode the response and extract the SAML assertion
    soup = BeautifulSoup(response.text, features="lxml")
    # print (response.text.decode('utf8'))
    # print ('************************************************************************************')
    assertion = ''
    
    # Look for the SAMLResponse attribute of the input tag (determined by
    # analyzing the debug print lines above)
    for inputtag in soup.find_all('input'):
        if(inputtag.get('name') == 'SAMLResponse'):
            # print(inputtag.get('value'))
            assertion = inputtag.get('value')
            break
        if (len(assertion) > 0):
            break
    
    # Better error handling is required for production use.
    if (assertion == ''):
        print('Response did not contain a valid SAML assertion')
        print('Check input values for name/password, or the validiity of idpentryurl: ' + idpentryurl)
        sys.exit(0)
    
    # Debug only
    # print "####################Saml Assertion###############################:"
    # print(assertion)
    # print "#################################################################:"
    # print(base64.b64decode(assertion))
    # print "#################################################################:"
    
    # Parse the returned assertion and extract the authorized roles
    awsroles = []
    root = ET.fromstring(base64.b64decode(assertion))
    for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
        if (saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'):
            for saml2attributevalue in saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
                awsroles.append(saml2attributevalue.text)
    
    # Note the format of the attribute value should be role_arn,principal_arn
    # but lots of blogs list it as principal_arn,role_arn so let's reverse
    # them if needed
    for awsrole in awsroles:
        chunks = awsrole.split(',')
        if'saml-provider' in chunks[0]:
            newawsrole = chunks[1] + ',' + chunks[0]
            index = awsroles.index(awsrole)
            awsroles.insert(index, newawsrole)
            awsroles.remove(awsrole)
    
    # If I have more than one role, ask the user which one they want,
    # otherwise just proceed
    print("")
    i = 0
    if (len(awsroles) == 0):
        print('This user is not configurad for any ADFS/ECS roles')
        sys.exit(1)
    
    print("Following provider role combination can be used with assertion provided with ECS assumerolewithsaml api")
    #
    # [ 0 ]:  urn:ecs:iam::s3:role/ADFS-AdminUser urn:ecs:iam::s3:saml-provider/HadoopProvider
    #
    for awsrole in awsroles:
        role=awsrole.split(',')[0]
        provider=awsrole.split(',')[1]
        print('[', i, ']: ', role, provider)
        i += 1    
    
    print("Enter the number for the role to assume (between 0 and " + str(len(awsroles)-1) + "): ", end=' ')
    role_number = input()
    
    if (int(role_number) < 0 or int(role_number) > len(awsroles)-1):
        print(('Invalid input: ' + role_number))
        sys.exit(1)
    
    role = awsroles[int(role_number)].split(',')[0]
    provider = awsroles[int(role_number)].split(',')[1]
    
    print(('You chose role ' + role + ' and provider ' + provider))
    
    payload={}
    
    payload['Action'] = 'AssumeRoleWithSAML'
    payload['RoleArn'] = role
    payload['PrincipalArn'] = provider
    payload['DurationSeconds'] = duration_seconds
    payload['SAMLAssertion'] = assertion
    # Debug only
    # print ('https://' + iamprovider + ':4443/iam')
    # print payload
    response = session.post('https://' + iamprovider + '/iam', data=payload, verify=sslverification)

    # Debug
    # print (response.text)
    
    res = json.loads(response.text)
    
    if (res['status'] != "success"):
        print(("Failed to assume role: " + role))
        sys.exit(1)
    
    data = json.loads(res['data'])
    SecretAccessKey = data['AssumeRoleWithSAMLResult']['Credentials']['SecretAccessKey']
    SessionToken = data['AssumeRoleWithSAMLResult']['Credentials']['SessionToken']
    AccessKeyId = data['AssumeRoleWithSAMLResult']['Credentials']['AccessKeyId']

    # Convert Expiration (UTC) to local time
    # e.g. 2020-03-18T22:26:58Z to local time relative to UTC
    Expiration = data['AssumeRoleWithSAMLResult']['Credentials']['Expiration']

    print(("Access Key: " + AccessKeyId))
    print(("Secret Key: " + SecretAccessKey))
    print(("Session Token: " + SessionToken))
    print(("Expiration Date (UTC): " + Expiration))
    print()

    print(("Use these Hadoop settings: -D fs.s3a.secret.key="+SecretAccessKey + " -D fs.s3a.access.key=" + AccessKeyId + " -D fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider -D fs.s3a.session.token=" + SessionToken))

