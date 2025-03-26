#!/bin/sh

eval $custom_host

helpFunction()
{
   echo ""
   echo "Usage: $0 -c config-path -mongo ENV_MONGO_URI --elsurl ENV_ELS_URL --elsuser ENV_ELS_USER --elspass ENV_ELS_PASS"
   echo -e "\t-c path template file config"
   echo -e "\t--mongo ENV MONGO URI of module (grant user with database monstache)"
   echo -e "\t--elsurl ENV ElasticSearch URL of module"
   echo -e "\t--elsuser ENV ElasticSearch username of module"
   echo -e "\t--elspass ENV ElasticSearch password of module"
   exit 1 # Exit script after printing help
}

checkExistElsIndex()
{
  if [ -z "$ELS_USER" ] && [ -z "$ELS_PASS" ]
  then
      response=$(curl --write-out '%{http_code}' --silent --output /dev/null "$ELS_URL/$INDEX")
  else
      response=$(curl --user "$ELS_USER:$ELS_PASS" --write-out '%{http_code}' --silent --output /dev/null "$ELS_URL/$INDEX")
  fi
  echo $response
}

SHORT=c:,m:,e:,i:,f:,g
LONG=config:,mongo:,elsurl:,elsuser:,elspass:
OPTS=$(getopt --alternative --options $SHORT --longoptions $LONG -- "$@")

eval set -- "$OPTS"

while :
do
  case "$1" in
    -c | --config )
      CONFIG_PATH="$2"
      shift 2
      ;;
    -m | --mongo )
      MONGO_ENV="$2"
      shift 2
      ;;
    -e | --elsurl )
      ELS_URL="$2"
      shift 2
      ;;
    -f | --elsuser )
      ELS_USER="$2"
      shift 2
      ;;
    -g | --elspass )
      ELS_PASS="$2"
      shift 2
      ;;
    --)
      shift;
      break
      ;;
    *)
      echo "Unexpected option: $1"
      exit 1
      ;;
  esac
done

# Print helpFunction in case parameters are empty
if [ -z "$CONFIG_PATH" ] || [ -z "$MONGO_ENV" ] || [ -z "$ELS_URL" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

if [[ ! -f $CONFIG_PATH ]]; then
    echo "$CONFIG_PATH does not exist."
    exit 1
fi

MONGO_URI=`printenv $MONGO_ENV`
if [ -z $MONGO_URI ]
then
  echo "MONGO_URI empty"
  exit 1
fi
count_mongo=$(echo $MONGO_URI | grep -c "27017")
if [ $count_mongo -gt 1 ] && [ $MONGO_URI != *"readPreference"* ]
then
  MONGO_URI="$MONGO_URI\&readPreference=secondaryPreferred"
fi

echo $MONGO_URI

ELS_URL=`printenv $ELS_URL`
if [ -z "$ELS_URL" ]
then
  ELS_URL=$ELASTIC_SEARCH_HOST:$ELASTIC_SEARCH_PORT
fi
if [ ! -z "$ELS_USER" ] && [ ! -z "$ELS_PASS" ]
then
  ELS_USER=`printenv $ELS_USER`
  ELS_PASS=`printenv $ELS_PASS`
fi

if [ ! -z "$ELS_USER" ] && [ ! -z "$ELS_PASS" ]
then
  ELS_CONN=`curl --user "$ELS_USER:$ELS_PASS" "$ELS_URL/_nodes/_all/http?pretty" 2>&1 | grep "publish_address" | awk '{print($3)}' | sed -E 's@^"([^"]+)",@"http://\1"@g' | tr '\n' ',' | head -c -1`
else
  ELS_CONN=`curl "$ELS_URL/_nodes/_all/http?pretty" 2>&1 | grep "publish_address" | awk '{print($3)}' | sed -E 's@^"([^"]+)",@"http://\1"@g' | tr '\n' ',' | head -c -1`
fi

mkdir -p /tmp
cp $CONFIG_PATH /tmp

file_name="${CONFIG_PATH##*/}"

sed -i "s#__MONGODB_URL__#$MONGO_URI#" /tmp/$file_name
sed -i "s#__ELS_CONN__#$ELS_CONN#" /tmp/$file_name
sed -i "s#__ELASTIC_SEARCH_USER__#$ELS_USER#" /tmp/$file_name
sed -i "s#__ELASTIC_SEARCH_PASSWORD__#$ELS_PASS#" /tmp/$file_name

INDEX=`grep "index=" /tmp/$file_name | cut -d "=" -d '"' -f2`
i=0
while true
do
  let i++
  response=$( checkExistElsIndex )
  if [ $response == '200' ]
  then
    /bin/monstache -f /tmp/$file_name
  elif [ $i == 10 ]
  then
    echo "index $INDEX not found. Checked $i"
    exit 1
  else
    echo "index $INDEX not found. Checked $i"
    sleep 30s
  fi
done
