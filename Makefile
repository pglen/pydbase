#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#  OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.
#

.PHONY:  doc clean echo tests

PROG=pydbase

all:
	@echo "Targets: clean cleandata tests pipupload"
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
	./pip-upload.py

tests:
	cd tests; pytest

setup:
	@python3 ./setup.py install

build:
	@python3 ./setup.py build

remove:
	@python3 ./setup.py install --record files.txt
	xargs rm -rf < files.txt
	@rm -f files.txt

clean:
	@rm -f *.pyc
	@rm -f pedlib/*.pyc
	@rm -rf ./pydbase/__pycache__
	@rm -rf build/*
	@rm -rf dist/*

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


pgit:
	git add .

	DDD = $(shell bash -c 'read -p "Commit Message: " commit; echo $$commit')
	echo "Committing as $(DDD)"

	git commit -m "$(DDD)"
	git push
	#git push local

git:
	git add .
	git commit -m "$(AUTOCHECK)"
	git push
	#git push local

doc:
	@pdoc --logo image.png  \
                -o doc `find . -maxdepth 2 -name  \*.py`

doxy:
	doxygen

# End of Makefile
