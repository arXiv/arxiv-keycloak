
include ../.env
export $(shell sed 's/=.*//' ../.env)


.PHONY: all bootstrap 

all: bootstrap

bootstrap: development

development:
	git clone https://github.com/arXiv/arxiv-base.git
	cd arxiv-base && git switch develop && git checkout 83af5ee568c5710ca3df0f6f68e39f998a772fa8 && mv development ../
	rm -fr ./arxiv-base
