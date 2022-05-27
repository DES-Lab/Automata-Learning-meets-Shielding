#!/bin/bash

# to be executed in *world_output

SUMMARY="csv"
temp="temp"

rename no_penalty no *.log

for setting in penalty shielded; do
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
  mins=$(awk -F';' '{
          s=10000;
          numFields=-1;
          for(i=2; i<=NF;++i){
            curr=$i + 0
            if(curr<s) {
              s=curr;
            }
            numFields++
          }
          print s ";"}' $SUMMARY)
  maxs=$(awk -F';' '{
          s=-10000;
          numFields=-1;
          for(i=2; i<=NF;++i){
            curr=$i
            if(curr>s) {
              s=curr;
            }
            numFields++
          }
          print s ";"}' $SUMMARY)

  echo "" >> $SUMMARY
  echo $averages >> $SUMMARY
  echo $mins >> $SUMMARY
  echo $maxs >> $SUMMARY
  mv $SUMMARY ${setting}_${SUMMARY}.csv
done
rm $temp
