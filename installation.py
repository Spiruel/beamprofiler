#this script is invoked via cmd. it installs BiLBO into your working dir.
import pip, os, urllib2
import zipfile, StringIO

requirements = [line for line in urllib2.urlopen('https://raw.githubusercontent.com/Spiruel/beamprofiler/master/requirements.txt')] + ['requests']

def install(package):
    pip.main(['install', package])
            
proceed = raw_input('Accepting the following will install BiLBO into the working directory of your machine. Do you wish to continue? y/n ')
if proceed.lower() in ['yes','y','yeah','yup','ya','oui','si','yesicompletelyagree','anykey','whereistheanykey']:
    for package in requirements:
        if 'Pillow' in package: package = 'Pillow'
        if 'PyAudio' in package: package = 'pyaudio'
        try:
            __import__(package.split('==')[0])
            print('Success with package, ' + package)
        except ImportError, e:
            install(package) # module doesn't exist, deal with it.
            try:
                __import__(package)
                print('Success with package, ' + package)
            except ImportError, e:
                print('Still could not import package ' + package + '. Please install this manually!')
                
    source_filename = os.getcwd()+'\Spiruel-beamprofiler-54ba931'
    if not os.path.exists(source_filename):
        zip_file_url = 'https://github.com/Spiruel/beamprofiler/zipball/master/'
        file_name = 'BiLBO'
        print('Downloading files...')
        import requests
        r = requests.get(zip_file_url, stream=True)
        z = zipfile.ZipFile(StringIO.StringIO(r.content))
        z.extractall()
        
    else:
        print('\nzip already in working directory!')

    try:
        import cv2
        print('\n>>>BiLBO should now be fully installed onto your computer (under Spiruel-beamprofiler-*******). Simply run get_profiler.py!')
    except:
        print('\n>>>BiLBO should now be downloaded onto your computer (under Spiruel-beamprofiler-*******). \nYou have not yet installed OpenCV and will need to do so in order for the programme to work.')
else:
    print('Aborting installation :\'(')
    raise SystemExit(0)