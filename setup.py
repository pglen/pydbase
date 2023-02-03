import setuptools

descx = '''PyEdPro is modern multi-platform editor. Simple, powerful,
configurable, extendable. Goodies like macro recording / playback, spell check,
column select, multiple clipboards, unlimited undo ...
   PyEdPro.py has macro recording/play, search/replace, one click function navigation,
auto backup, undo/redo, auto complete, auto correct, syntax check, spell suggestion
 ... and a lot more.
   The recorded macros, the undo / redo information the editing session details persist
 after the editor is closed.
    The spell checker can check code comments. The parsing of the code is
rudimentary, comments and strings are spell checked. (Press F9 or Shit-F9) The code is filtered
out for Python and  'C'. The spell checker is executed on live text. (while typing)
'''

classx = [
          'Development Status :: Mature',
          'Environment :: GUI',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Editors',
          'Topic :: Software Development :: Editor',
        ]

includex = ["*", "pedlib/", "panglib", "pedlib/images",
            "image.png", "pyedpro_ubuntu.png"]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pydbase",
    version="1.0",
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
    include_package_data=True,
    packages=setuptools.find_packages(include=includex),

    scripts = ['pydbase.py', ],

    python_requires='>=3',
    entry_points={
        'console_scripts': [ "pyedpro=pydbase:mainfunc", ],
    },
)

# EOF
