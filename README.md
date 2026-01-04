## clean_pdb.py usage
### Execute without selecting any chain in particular from original pdb
python ~/cnic/rosetta_cm_utils/clean_pdb.py COX4I1_homo_sapiens.pdb ignorechain

### Execute rename pdbs and files to match
#TODO: add script to remove ignore chain from files (pdbs and fastas) after cleaning, removing uncleaned pdbs and using same name for header > in fastas

## ClustalO launch
### Create fasta with 3 sequences
cat *.fasta > COX4I1_gg_hs_mm.fasta
### Run clustal using clustalo docker client 
docker run --rm -it -v `pwd`:/results -w /results ebiwp/webservice-clients clustalo.py --email casimon@cnic.es --stype protein --sequence COX4I1_gg_hs_mm.fasta

## clustal_to_grishin.py usage
python clustal_to_grishin.py examples/convert_aln_to_grishin/COX3gg_COX3hs.aln  --target-id "COX3gg"   --template-id "COX3hs"   --target-name COX3gg   --template-name COX3hs   -o COX3gg_COX3hs.grishin

## TOPCONS launch
### get_span_file.py usage
python3 /home/csimon/cnic/rosetta_cm_utils/get_span_file.py --topcons-script /home/csimon/cnic/rosetta_cm_utils/topcons_launch.py    --seq /home/csimon/cnic/rosetta_cm_utils/examples/topcons/COX3gg.fasta     --output-topcons /home/csimon/cnic/rosetta_cm_utils/examples/topcons/output_topcons     --jobname COX3_gg     --poll 60  --octopus-out /home/csimon/cnic/rosetta_cm_utils/examples/topcons/

### octopus_launch.py usage
python octopus2span.py examples/topcons/COX3gg.octopus -o examples/topcons/COX3gg.span

## threading_over_template.py usage
python threading_over_template.py --fasta examples/threading/COX3gg.fasta --alignment examples/threading/COX3gg_COX3hs.grishin --template examples/threading/COX3hs.pdb --out examples/threading/ --rosetta-bin ~/cnic/rosetta3.10/rosetta-3.10/main/source/bin/partial_thread.static.linuxgccrelease 