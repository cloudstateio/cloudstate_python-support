#!/usr/bin/env bash
set -o errexit

RUN_SUFFIX=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)

PROXY_NAME=cloudstate-proxy-$RUN_SUFFIX
USER_FUNCTION_NAME=cloudstate-function-$RUN_SUFFIX
FUNCTION_CLIENT_NAME=cloudstate-function-client-$RUN_SUFFIX

TCK_NAME=cloudstate-tck-$RUN_SUFFIX
PYTHON_TCK_NAME=cloudstate-python-tck-dev:$RUN_SUFFIX

TCK_IMAGE=cloudstateio/cloudstate-tck:latest
PROXY_IMAGE=cloudstateio/cloudstate-proxy-dev-mode:latest

echo using TCK image $TCK_IMAGE
echo using proxy image $PROXY_IMAGE

NETWORK_NAME=tck-network-$RUN_SUFFIX

finally() {
    docker rm -f $PROXY_NAME
    docker rm -f $USER_FUNCTION_NAME
    docker rm -f $FUNCTION_CLIENT_NAME
    docker rmi $PYTHON_TCK_NAME

    docker network rm $NETWORK_NAME
}
trap finally EXIT
set -x

#  fresh docker build
docker build -t $PYTHON_TCK_NAME ./

docker network create $NETWORK_NAME

#  primary tck tests for shopping cart
docker run -d --network $NETWORK_NAME --name $USER_FUNCTION_NAME -p 8080:8080 $PYTHON_TCK_NAME server shoppingcart
docker run -d --network $NETWORK_NAME --name $PROXY_NAME -p 9000:9000 \
    -e USER_FUNCTION_HOST=$TCK_NAME \
    -e USER_FUNCTION_PORT=8090 \
    $PROXY_IMAGE \
    -e HTTP_PORT=9000
docker run --rm --network $NETWORK_NAME --name $TCK_NAME -p 8090:8090 \
    -e TCK_HOST=0.0.0.0 \
    -e TCK_PORT=8090 \
    -e TCK_PROXY_HOST=$PROXY_NAME \
    -e TCK_PROXY_PORT=9000 \
    -e TCK_SERVICE_HOST=$USER_FUNCTION_NAME \
    -e TCK_SERVICE_PORT=8080 \
    $TCK_IMAGE

status=$?
docker container logs $PROXY_NAME
docker container logs $USER_FUNCTION_NAME

echo "Removing docker containers"
docker rm -f $PROXY_NAME
docker rm -f $USER_FUNCTION_NAME

#  secondary integration tests for stateless function:
docker run -d --network $NETWORK_NAME --name $USER_FUNCTION_NAME -p 8080:8080 $PYTHON_TCK_NAME \
    server \
    ActionDemo \
    shoppingcart
sleep 5
docker run -d --network $NETWORK_NAME --name $PROXY_NAME -p 9000:9000 \
    -e USER_FUNCTION_HOST=$USER_FUNCTION_NAME \
    -e USER_FUNCTION_PORT=8080 \
    $PROXY_IMAGE
sleep 5
docker run --network $NETWORK_NAME --name $FUNCTION_CLIENT_NAME $PYTHON_TCK_NAME \
    client \
    server_host $PROXY_NAME \
    ActionDemo \
    shoppingcart

status1=$?


RETURNSTATUS=1
if [ "${status1}" == 0 ] && [ "${status}" == 0 ]; then
  RETURNSTATUS=0
fi


exit $RETURNSTATUS
