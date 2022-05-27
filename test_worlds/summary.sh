#!/bin/bash

SUMMARY="csv"
temp="temp"

rename no_penalty no *.log

for setting in no penalty shielded; do
  touch $SUMMARY
  for f in *${setting}*log; do
    curr=$(grep "Avg. re" $f | awk '{ printf "%s\n", $3}')
    echo "$curr" | paste -d ";" $SUMMARY - > $temp
    cp $temp $SUMMARY
  done
  averages=$(awk -F';' '{
          s=0;
          numFields=-1;
          for(i=1; i<=NF;++i){
            s+=$i;
            numFields++
          }
          print s/numFields ";"}' $SUMMARY)

  echo "" >> $SUMMARY
  echo $averages >> $SUMMARY
  mv $SUMMARY ${setting}_${SUMMARY}.csv
done
rm $temp
