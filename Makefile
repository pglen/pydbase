#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#  OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.
#

.PHONY:  help doc clean echo tests docs doc

# Minimal makefile for Sphinx documentation
# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
#%: Makefile
#	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

PROG=pydbase

all:
	@echo "Targets: clean cleandata tests pipupload docs"
	@echo "Type 'make help' for a list of targets"

help:
	@echo
	@echo "Targets:"
	@echo "	 make clean        -- Clean Executables"
	@echo "	 make cleandata    -- Remove test databases"
	@echo "	 make build"
	@echo "	 make setup        -- Run the setup.py script as install "
	@echo "	 make tests        -- execute test suite ${PROG}"
	@echo "	 make doc          -- create ${PROG} documentation"
	@echo "	 make tests        -- execute ${PROG} test suite"
	@echo "	 make doxy         -- create ${PROG} documentation"
	@echo

pipupload:
	./pip-build.py
	./pip-upload.sh

tests:
	cd tests; pytest

setup:
	@python3 ./setup.py install

build:
	@python3 ./setup.py build

clean:
	@rm -f *.pyc
	@rm -f pedlib/*.pyc
	@rm -rf ./pydbase/__pycache__
	@rm -rf build
	@rm -rf _build
	@rm -rf dist
	@rm -f pydbase.p*
	@rm -f pydbchain.p*

cleandata:
	@rm -f pydbase.pydb
	@rm -f pydbase.pidx
	@rm -f pydbase.lock
	@rm -f pydbase.ulock
	@rm -f pydbchain.pydb
	@rm -f pydbchain.pidx
	@rm -f pydbchain.lock
	@rm -f pydbchain.ulock

echo:
	@echo Echoing: ${AUTOCHECK}

# Auto Checkin
ifeq ("$(AUTOCHECK)","")
AUTOCHECK=autocheck
endif

#echo $(bash 'read -p "Commit Message: " commit ; echo ${commit}')

promptx:
	echo aaaa
	echo `echo sss`
	echo "Committing as ${commit}"

pgit: promptx
	echo "in pgit" ${DDD}
	#git add .
	#git commit -m "$(DDD)"
	#git push
	#git push local

git:
	git add .
	git commit -m "$(AUTOCHECK)"
	git push
	#git push local


XPATH=PYTHONPATH=../pyvcommon:../  python -W ignore::DeprecationWarning `which pdoc3` --force --html

docs:
	@${XPATH}  -o pydbase/docs pydbase/twinchain.py
	@${XPATH}  -o pydbase/docs pydbase/twincore.py
	@${XPATH}  -o pydbase/docs pydbase/twinbase.py
	@${XPATH}  -o pydbase/docs chainadm.py
	@${XPATH}  -o pydbase/docs dbaseadm.py

doxy:
	doxygen

install:
	@echo installing pydbase manual file
	sudo install man/man1/pydbase.1 /usr/share/man/man1

pipup:
	./pip-build.py
	./pip-upload.sh


# End of Makefile
