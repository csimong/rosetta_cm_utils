#!/bin/bash

#
# Script:        convert_aln_to_grishin.sh
# Description:   Convert .aln files from ClustalO to .grishin format
#
# Originally created by:
#   Name:        Laura Cano Almarza
#   Date:        2024-07-12
#
# Maintained by:
#   Name:        Carolina Simón Guerrero
#   Email:       carolina.simon.guerrero@gmail.con
#   Since:       2025-12-23
# 
# Institution:
#   Name:        Spanish National Centre for Cardiovascular Research - CNIC
#   Unit/Group:  Functional Genetics of the Oxidative Phosphorylation System (GENOXPHOS) Lab
#   Address:     Madrid, Spain
#   Website:     https://www.cnic.es/en/investigacion/functional-genetics-oxidative-phosphorylation-system-genoxphos
#
# Repository/URL: https://github.com/csimong/rosetta_cm_utils
#
# Notes:
# - Usage: ./conver_aln_to_grishin.sh <alignment_file.aln> <target_seq.fasta> <template_seq.fasta>
# - Usage example: ./conver_aln_to_grishin.sh COX3gg_COX3hs.aln COX3gg.fasta COX3hs.fasta
# - Input formats: sequence names in .fasta and id in .aln must match. See /examples folder for more info.


#Arguments
alignment_file="$1" && echo "Alignment file = ""$1"
target_file="$2" && echo "Target sequence = ""$2"
template_file="$3" && echo "Template sequence = ""$3"

target_file_name="${target_file%.*}"    # Keep just file name
template_file_name="${template_file%.*}"    # Keep just file name


#Creates grishin file
echo "## ""$target_file_name"" ""$template_file_name"".pdb">grishin_file
echo "#">>grishin_file
echo "scores from program: 0">>grishin_file

#Processes target sequence
# Processes target and template sequences from alignment file
echo "0 " >> grishin_file_target
echo "0 " >> grishin_file_template

target_seq="0 "

while IFS= read -r line; do
    if [[ "$line" == "${target_file_name}"* ]]; then
        new=$(echo "$line" | sed -e "s#${target_file}      ##g" -e "s/\t.*//")
        target_seq="$target_seq""$new"
    elif [[ "$line" == "${template_file_name}"* ]]; then
        echo "$line" | sed -e "s#${template_file}      ##g" | cut -c 1-60 >> grishin_file_template
    fi
done < "$alignment_file"

#Adds sequence to grishin_file
cat grishin_file grishin_file_target grishin_file_template > structure.grishin 
#rm grishin_file grishin_file_target grishin_file_template

#Warning about further formatting
echo ""
echo "WARNING!"
echo "Note that your file needs still formatting"
echo "  (1) Remove final numbers"
echo "  (2) Put everything in the same line"


# Improvements: 
#sed -e "s/\t.*//" 
