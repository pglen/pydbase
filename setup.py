import setuptools
import os, sys

descx = '''
        It is an insanely simple database. Fast. If all you need is a key / value
        pair, this is the perfect solution.
        (Yes, all you need is a key / value pair, as any and every structure
        can be built out of it)
'''

classx = [
          'Development Status :: Mature',
          'Environment :: GUI',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Databases',
        ]
# Get version number  from the server support file:
fp = open("pydbase/twinbase.py", "rt")
vvv = fp.read(); fp.close()
loc_vers =  '1.0.0'     # Default
for aa in vvv.split("\n"):
    idx = aa.find("VERSION =")
    if idx == 0:        # At the beginning of line
        try:
            loc_vers = aa.split()[2].replace('"', "")
            break
        except:
            pass
#print("loc_vers:", loc_vers)

includex = ["*", "pydbase/", ]

doclist = []; droot = "pydbase/docs/"
doclistx = os.listdir(droot)
for aa in doclistx:
    doclist.append(droot + aa)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pydbase",
    version=loc_vers,
    author="Peter Glen",
    author_email="peterglen99@gmail.com",
    description="High speed database with key / data in python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pglen/pydbase",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(include=includex),
    scripts = ['dbaseadm.py', 'chainadm.py'],
    py_modules = ["pyvpacker",],
    include_package_data=True,
    package_data = {"pydbase" : doclist},
    #data_files = {"man/man1/pydbase.1"},
    python_requires='>=3',
    entry_points={
        'console_scripts': [ "dbaseadm=dbaseadm:mainfunc",
                                "chainadm=chainadm:mainfunc",
                           ],
    },
)

# EOF
