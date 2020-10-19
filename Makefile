AWS := aws
STACK_NAME := cfn-boto
export AWS STACK_NAME

help:
	@echo
	@echo 'CLoudFormation Boto Interface Make System'
	@echo '-----------------------------------------'
	@echo
	@echo 'Synopsis: make deploy [STACK_NAME=$(STACK_NAME)]'
	@echo
	@echo 'The following make targets are currently supported:'
	@echo
	@echo 'help	- You are reading this now :)'
	@echo
	@echo 'build	- Retrieves all dependencies and installs them into lib/'
	@echo
	@echo 'package	- Packages the Lambda file and its dependencies into a zip archive'
	@echo
	@echo 'deploy	- Deploys the whole stack into the AWS Cloud (this target performs'
	@echo '	  a quick and dirty check on whether you are authenticated to AWS'
	@echo '	  or not, however if this check does not work for you you can skip'
	@echo '	  it by specifying SKIP_AUTH_CHECK=1 on the make command line)'
	@echo
	@echo 'Likely, you will just use "make deploy" and it will do everything for you!'
	@echo
	@echo 'When using "make deploy" the following make variables are recognised and'
	@echo 'supported:'
	@echo
	@echo 'STACK_NAME - The name of the CloudFormation stack to be created'
	@echo '	  (Default: $(STACK_NAME))'
	@echo
	@echo 'Have fun!'
	@echo

venv: auto/virtualenv
.build: auto/virtualenv
.build/bin: auto/virtualenv
.build/lib/*: auto/virtualenv
auto/virtualenv: requirements.txt
	@$@

build: auto/prepare-deps lambda.zip
lib: auto/prepare-deps
auto/prepare-deps: auto/virtualenv .build .build/bin .build/lib/*
	@$@

package: lambda.zip
lambda.zip: auto/package-lambda
auto/package-lambda: auto/prepare-deps lib src
	@$@

aws-auth: # You can suppress this check by calling make with SKIP_AUTH_CHECK=1
	@auto/check-aws-auth

check: aws-auth lambda.template
	@auto/check lambda.template

deploy: aws-auth check auto/deploy
auto/deploy: auto/package-lambda lambda.zip lambda.template FORCE
	@$@ "$(STACK_NAME)"

clean:
	@echo 'Cleaning up:'
	@rm -rvf .build lib lambda.zip lambda.template.packaged
	@echo 'Complete'

.DEFAULT: help

FORCE:

# A couple of helper macros to check for undefined variables
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
        $(error Undefined $1$(if $2, ($2))$(if $(value @), \
                required by target `$@' -- please check "make help")))

