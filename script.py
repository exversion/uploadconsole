import requests
import sys, argparse

SESSION = ''

def login(username, password):
    # This is the form data that the page sends when logging in
    login_data = {
        'loginemail': username,
        'loginpswd': password,
        'submit': 'login',
    }

    # Authenticate
    r = requests.post('http://www.exversion.com/command/login'
, data=login_data)

    # Try accessing a page that requires you to be logged in
    #r = session.get('http://friends.cisv.org/index.cfm?fuseaction=user.fullprofile')
    vars(r.json())
    
    
#    files = {'file1': open('report.xls', 'rb'), 'file2': open('otherthing.txt', 'rb')}
#    r = requests.post('http://httpbin.org/post', files=files)

def main():
    #Parse arguments
     parser = argparse.ArgumentParser()
     parser.add_argument('-u', '--username', required=True)
     parser.add_argument('-p', '--password', required=True)
     parser.add_argument('-f', '--file', required=True)
     
     ######## More Options ######
     ## Specify a default
     # parser.add_argument('-f', '--my-foo', default='foobar')
     ##
     ## Define flag as T/F
     # parser.add_argument('--foo', action='store_true')
     # parser.add_argument('--no-foo', action='store_false')
     ##
     ## Require
     # parser.add_argument('-o', '--output', required=True)
     
     args = parser.parse_args()
     login(args.username, args.password)
     

if __name__ == '__main__':
    main()