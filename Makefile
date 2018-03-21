.PHONY: help
envdir=$(notdir $(lastword $(shell pwd)))


help:
	@echo "  env         create a development environment using virtualenv"
	@echo "  deps        install dependencies using pip3"



env:
	if [ ! -d ~/.venvs/ ] ; then mkdir ~/.venvs; fi && \
	if [ -d ~/.venvs/$(envdir) ] ; then rm -rf ~/.venvs/$(envdir); fi
	if [ ! -d ~/.venvs/$(envdir) ] ; then python3 -m venv ~/.venvs/$(envdir); fi && \
	. ~/.venvs/$(envdir)/bin/activate && \
	if [ -s requirements.txt ]; then make deps; fi


env_pypy3:
	if [ ! -d ~/.venvs/ ] ; then mkdir ~/.venvs; fi && \
	if [ -d ~/.venvs/$(envdir) ] ; then rm -rf ~/.venvs/$(envdir); fi
	if [ ! -d ~/.venvs/$(envdir)_pypy3 ] ; then virtualenv ~/.venvs/$(envdir)_pypy3; fi && \
	. ~/.venvs/$(envdir)_pypy3/bin/activate && \
	if [ -s requirements.txt ]; then make deps_pypy3; fi



deps:
	pip3 install -U -r requirements.txt


deps_pypy3:
	pypy3 -m pip3 install -U -r requirements.txt


save_deps:
	pip3 freeze > requirements.txt



run:
	. ~/.venvs/$(envdir)/bin/activate && python main.py


run_pypy3:
	. ~/.venvs/$(envdir)_pypy3/bin/activate && pypy3 main.py
