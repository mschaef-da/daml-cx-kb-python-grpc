
asset_model_dar=./asset-model/.daml/dist/asset-model-0.0.1.dar

.PHONY: build
build: build-daml build-python                 ## Ensure the project is fully built and ready to run

.PHONY: build-daml

build-daml: ${asset_model_dar}
${asset_model_dar}: .damlsdk                   ## Build all Daml code in the project
	(cd asset-model && daml build)

.PHONY: test-daml
test-daml: build-daml                          ## Build all Daml code in the project
	(cd asset-model && daml test)

.PHONY: build-python
build-python: target/_gen/.gen                 ## Setup the Python Environment.

.PHONY: format-python
format-python: .venv                           ## Automatically reformat the Python code
	black python/*.py

.PHONY: clean
clean: stop-ledger                             ## Reset the build to a clean state without any build targets
	(cd asset-model && daml clean)
	rm -fr .damlsdk .protobufs target
	rm -fr python/__pycache__
	rm -frv log/*

.PHONY: clean-all
clean-all: clean                               ## Reset the build to a fully clean state, including the Python venv
	rm -rf .venv

.PHONY: venv
venv: .venv

.venv: requirements.txt
	mkdir -p target
	python3 -m venv .venv
	.venv/bin/pip3 install -r requirements.txt

.damlsdk: daml.yaml
	scripts/install-daml-sdk.sh $< $@

.protobufs: daml.yaml
	scripts/install-protobufs.sh $< $@ target

protobuf_tag = $(shell cat .protobufs)

target/_gen/.gen: .venv .protobufs
	mkdir -p target/_gen

	(cd target && unzip -o "protobufs-${protobuf_tag}.zip")

	.venv/bin/python3 -m grpc_tools.protoc \
	    -Ivendor \
		-I$$(find target -name "protos-*" -type d -print -quit) \
	    --python_out=target/_gen \
	    --pyi_out=target/_gen \
	    --grpc_python_out=target/_gen \
	    $$(find target -name "*.proto" -not -name "daml_lf*.proto") \
	    $$(find vendor -name "*.proto")

	touch target/_gen/.gen

.PHONY: start-ledger
start-ledger: target/canton.pid                ## Start a locally running sandbox ledger

target/canton.pid: test-daml .damlsdk
	scripts/start-ledger.sh ${asset_model_dar}

.PHONY: start-ledger
stop-ledger:                                   ## Stop the locally running sandbox ledger
	scripts/stop-ledger.sh

.PHONY: help
 help:	                                       ## Show list of available make targets
	@cat Makefile | grep -e "^[a-zA-Z_\-]*: *.*## *" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
