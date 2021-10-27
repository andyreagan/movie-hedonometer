HTMLFOLDER=data/scripts/html
OUTPUTFOLDER=data/scripts/html-cleaned

for HTML in $(\ls -1 ${HTMLFOLDER}/*.html); do
    FILE="$OUTPUTFOLDER/$(basename $HTML .html)"
    echo $FILE
    # sed -i "s/\"scrtext\"/scrtext/" $FILE
    grep -A 1000000 "class=\"scrtext\"" $HTML | sed "s/<tt>//" | sed -n '2,1000000p' > $FILE.end
    grep -B 1000000 -m 1 "</pre>" $FILE.end > $FILE.end.beg
    # SIZE=$(du -b $FILE.end.beg | cut -f1)
    # if [ $((SIZE)) -le 4000 ]; then
    #     echo "still failed first parse on $FILE"
    #     grep -B 1000000 -m 1 "</table>" $FILE.end > $FILE.end.beg
    # fi
    sed '$ d' $FILE.end.beg > $FILE.script.html
    rm $FILE.end.beg $FILE.end
    cat $FILE.script.html | sed -e "s/<b>//" | sed -e "s/<\/b>//" > $FILE.txt.clean00
    cat $FILE.script.html | sed -e "s/<[:\. -=?%#;\"'a-zA-Z0-9\n\\/]\{3,\}>//gi" > $FILE.txt.clean01
    cat $FILE.script.html | sed -e "s/<[^>]\{3,\}>//gi" > $FILE.txt.clean02
    cat $FILE.script.html | sed -e "s/<[.]\{3,\}>//gi" > $FILE.txt.clean03
    cat $FILE.script.html | sed -e "s/<[^>]\{2,\}>//gi" > $FILE.txt.clean04
    cat $FILE.script.html | sed -e "s/<[^b]{1}>//gi" > $FILE.txt.clean05
done






