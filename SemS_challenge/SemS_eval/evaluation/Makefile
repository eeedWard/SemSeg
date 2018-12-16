img=daravenox/temp-evaluator:latest

all: push

build:
	docker build -t $(img) .

define-challenge:
	dts challenges define --config ../challenge.yaml 

push: build
	docker push $(img)


