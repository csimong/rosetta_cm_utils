set encoding iso_8859_1
set xrange [1:261]
set yrange [0.83:1.25]
set autoscale xfix
set ter png enh interlace size 2400,840 font 'Nimbus,40'
set xlabel 'Position'
set ylabel 'Reliability           ' 
set ytics nomirror 0.5,0.1,1
set out '/static/tmp/tmp_ZmdiCj/rst_hqnbi8/seq_0///Topcons/topcons.large.png'
set tmargin 1.3
set lmargin 11.5
set rmargin 6.5
set label 'TOPCONS' font 'Nimbus,42' at screen 0.022,0.775
set object 1 rect from 0.5,1.1 to 14.5,1.108125 fc rgb "red" fs noborder
set object 2 rect from 58.5,1.1 to 81.5,1.108125 fc rgb "red" fs noborder
set object 3 rect from 147.5,1.1 to 157.5,1.108125 fc rgb "red" fs noborder
set object 4 rect from 220.5,1.1 to 238.5,1.108125 fc rgb "red" fs noborder
set object 5 rect from 35.5,1.135625 to 37.5,1.14375 fc rgb "blue" fs noborder
set object 6 rect from 102.5,1.135625 to 126.5,1.14375 fc rgb "blue" fs noborder
set object 7 rect from 178.5,1.135625 to 199.5,1.14375 fc rgb "blue" fs noborder
set object 8 rect from 259.5,1.135625 to 261.5,1.14375 fc rgb "blue" fs noborder
set object 9 rect from 14.5,1.1 to 35.5,1.14375 fc rgb "grey" fs noborder
set object 10 rect from 37.5,1.1 to 58.5,1.14375 fc rgb "white"
set object 11 rect from 81.5,1.1 to 102.5,1.14375 fc rgb "grey" fs noborder
set object 12 rect from 126.5,1.1 to 147.5,1.14375 fc rgb "white"
set object 13 rect from 157.5,1.1 to 178.5,1.14375 fc rgb "grey" fs noborder
set object 14 rect from 199.5,1.1 to 220.5,1.14375 fc rgb "white"
set object 15 rect from 238.5,1.1 to 259.5,1.14375 fc rgb "grey" fs noborder
set object 16 rect from 14.5,1.1 to 35.5,1.14375 fc rgb "grey" fs noborder
set object 17 rect from 37.5,1.1 to 58.5,1.14375 fc rgb "white"
set object 18 rect from 81.5,1.1 to 102.5,1.14375 fc rgb "grey" fs noborder
set object 19 rect from 126.5,1.1 to 147.5,1.14375 fc rgb "white"
set object 20 rect from 157.5,1.1 to 178.5,1.14375 fc rgb "grey" fs noborder
set object 21 rect from 199.5,1.1 to 220.5,1.14375 fc rgb "white"
set object 22 rect from 238.5,1.1 to 259.5,1.14375 fc rgb "grey" fs noborder
plot '/static/tmp/tmp_ZmdiCj/rst_hqnbi8/seq_0///Topcons/reliability.final' w l t '' lc rgb "black" lw 4
exit
