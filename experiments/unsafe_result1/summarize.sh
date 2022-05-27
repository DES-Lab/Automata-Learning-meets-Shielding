#/bin/zsh
for setting in penalty shielded; do
  SUMMARY=${setting}_learning_summary.csv
  rm -f $SUMMARY
  for f in **/${setting}_csv.csv; do
    echo $f >> $SUMMARY; tail -n 3 $f >> $SUMMARY;
  done
done
