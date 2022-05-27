#/bin/zsh
for setting in shielded; do
  SUMMARY=automata_sizes.csv
  rm -f $SUMMARY
  for f in **/${setting}_csv.csv; do
    echo $f >> $SUMMARY; tail -n 3 $f >> $SUMMARY;
  done
done
