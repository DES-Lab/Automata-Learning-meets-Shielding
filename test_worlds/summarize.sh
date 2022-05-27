#/bin/zsh
for setting in no penalty shielded; do
  SUMMARY=${setting}_summary.csv
  rm -f $SUMMARY
  for f in **/${setting}_csv.csv; do
    echo $f >> $SUMMARY; tail -n 1 $f >> $SUMMARY;
  done
done
