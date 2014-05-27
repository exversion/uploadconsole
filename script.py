import requests
import sys, argparse, csv, time, md5, random, os, re, json, hashlib
from colorama import init, Fore, Back, Style

BASE_URL = 'http://localhost/quantus/web/app_dev.php/'

def login(username, password, version):
    # This is the form data that the page sends when logging in
    login_data = {
        'username': username,
        'password': password,
        'submit': 'login',
        'version': version
    }

    # Authenticate
    r = requests.post(BASE_URL+'command/login/'
, data=login_data)

    # Is the version okay? 

    # Try accessing a page that requires you to be logged in
    #r = session.get('http://friends.cisv.org/index.cfm?fuseaction=user.fullprofile')
    return r.json()

    
#    files = {'file1': open('report.xls', 'rb'), 'file2': open('otherthing.txt', 'rb')}
#    r = requests.post('http://httpbin.org/post', files=files)

def space_available(available, used, actual):
    if (available-used) > actual:
        return True
    else:
        return False

def clean_data(data):
    item = {}
    for k in data.keys():
        if data[k] is not None:
            value = data[k]
        else:
            value = ''
        k = k.lower()
        k = k.strip()
        if k == '':
            k = 'autocolumn_'+random.randint()
        if k ==  "sets":
            k = "sets_"
        if k == "extension":
            k = "extension_"
        if k == "key":
            k = "key_"
        k = re.sub("#", "num", k)
        k = re.sub(r'[^A-Za-z0-9_ ]', "", k)
        k = re.sub(r'\s', "_", k)
        k = re.sub(r'^_', "!", k)
        item[k] = value
    return item

def prep_data(token, item, dataset, extension):
    item = clean_data(item)
    item['_hash'] = hashlib.md5(json.dumps(item)).hexdigest()
    item['extension'] = extension
    item['sets']=[dataset]
    item['_id']= dataset+str(random.randint(1,99))+str(time.time())
    return item 

def process_file(token, f, dataset, extension):
    reader = csv.DictReader(f)
    i = 0
    j = 1
    for row in reader:
        if i == 0:
            export = open('data/'+dataset+'-'+str(j), 'w')
            export.write(unicode('['))
        item = prep_data(token, row, dataset, extension)
        if item:
            #1048576
            #Check file size after each write
            #When limit is reached, set cap and write the rest of the files
            try:
                if i > cap:
                    export.write(unicode(json.dumps(item)))
                    export.write(unicode(']'))
                    i = 0
                    j = j + 1
                    export.close()
                else:
                    export.write(unicode(json.dumps(item))+',')
                    i += 1
            except NameError:
                size = export.tell()
                if size > 3145728:
                    cap = i
                    export.write(unicode(json.dumps(item)))
                    export.write(unicode(']'))
                    i = 0
                    j = j + 1
                    export.close()
                else:
                    export.write(unicode(json.dumps(item))+',')
                    i += 1

    return "%s files written" % (j,)

def chunks(data):
    return [data[x:x+5] for x in xrange(0, len(data), 5)]

def send_files(token, dataset):
    pdata = {'session': token,'dataset': dataset}
    for dirname, folders, files in os.walk('data'):
        packages = chunks(files)
        for p in packages:
            #fdata = {'session': token,'dataset': dataset}
            fdata = dict()
            i = 1
            for f in p:
                fdata['file'+str(i)] = open('data/'+f, 'rb')
                i += 1
            r = requests.post(BASE_URL+'command/upload/', files=fdata, data=pdata)
            try:
                if not r.json()['success']:
                    sys.exit(r.json()['message'])
            except:
                print r.text
    
        for fl in files:
            os.remove("data/"+fl)
    return True;

def yes_or_no(input):
    yes = set(['yes','y', 'ye', ''])

    if input.strip() in yes:
        return True
    else:
        return False

def create_dataset(session, file_path):
    title = '';
    while not title:
        sys.stdout.write('What is the name of this dataset? ')
        sys.stdout.write(Fore.GREEN + Style.BRIGHT)
        title = raw_input().lower()
        print(Fore.RESET + Back.RESET + Style.RESET_ALL)
    
    sys.stdout.write('Write a description:')
    print(Fore.GREEN + Style.BRIGHT)
    description = raw_input().lower()
    print(Fore.RESET + Back.RESET + Style.RESET_ALL)

    if session['level'] > 0:
        print 'Keep this data private? [y/n]'
        private = yes_or_no(raw_input().lower())
    else:
        private = 0;

    #Check to see if user can create private repos
    ds_data = {
        'username': session['username'],
        'user_id': session['user_id'],
        'title': title,
        'description': description,
        'private': private,
        'session': session['token'],
    }

    #Confirm
    if private:
        print 'Got it. Create a private dataset from %s named "%s" with description "%s" under user account %s? [y/n]' % (file_path, title, description, session['username'])
    else: 
        print 'Got it. Create a dataset from %s named "%s" with description "%s" under user account %s? [y/n]' % (file_path, title, description, session['username'])
    
    if yes_or_no(raw_input().lower()):   
        # Authenticate
        r = requests.post(BASE_URL+'command/create/'
, data=ds_data)

        return r.json()
    else:
        sys.exit('Upload cancelled.')


def main():
    #Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-f', '--file', required=True)
    parser.add_argument('-e', '--existing', default=False)
    parser.add_argument('--update', default=False)
     
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
    

    ### Check for update command first
    ## Pull latest version from github


    version = 0.01

    args = parser.parse_args()
    session = login(args.username, args.password, version)
    if not session['success']:
        sys.exit('Error: Login failed')

    #Does the file exist?
    try:
        with open(args.file) as f:
            size = os.fstat(f.fileno()).st_size
            ######
            #If the file is really big we should create a new collection for it.
            ######
            if space_available(session['space_available']*1048576, session['space_used']*1048576, size):
                if args.existing:
                    dataset = extend_dataset(session, args.files, args.existing)
                    extension = dataset['extension']
                else:
                    dataset = create_dataset(session, args.file)
                    extension = []
                #Option to upload to an existing dataset
                if dataset['success']:
                    print process_file(session['token'], f, dataset['dataset'], extension)
                    if send_files(session['token'],dataset['dataset']):
                        print 'Data successfully sent to Exversion and will be available once processed.'
                else:
                    sys.exit('Error: Token invalid')
            else:
                sys.exit('Error: Your account does not have enough space. Please contact us.')
    except IOError:
        sys.exit('Error: File does not exist')

if __name__ == '__main__':
    init()
    main()