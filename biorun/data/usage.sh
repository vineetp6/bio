#
# This script is used to generate Python tests.
#
# The output generated by each test can be seen at:
#
# https://github.com/ialbert/bio/tree/master/test/data
#

# Stop on errors.
set -uex

# Get data from NCBI
bio fetch NC_045512 MN996532 > genomes.gb

# Parse the standard input.
echo NC_045512 | bio fetch > sars2.gb

# Selecting by gene id
bio fasta genomes.gb --type gene --id N --end 10 > ids.fa

# Selecting all items
bio fasta genomes.gb --type all -end 10 > all.fa

# Slice the genomes
bio fasta genomes.gb --end  100 > genomes.fa

# Should produce the same output
cat genomes.gb | bio fasta --end  100 > genomes.fa

# Slice the genomes
bio fasta genomes.gb --end  100  --alias alias.txt > genomes.alias.fa

# Generate features only.
bio fasta genomes.gb --end 10 --type CDS > cds.fa

# Translate the features.
bio fasta genomes.gb --type CDS --translate > translate.fa

# Translate in a frame
bio fasta GATTACA --frame -3 --translate > frame.fa

# Extract the proteins.
bio fasta genomes.gb  --protein > protein.fa

# Start codons
cat cds.fa | bio fasta -e -3 > start.fa

# Last codons
cat cds.fa | bio fasta -s -3 > stop.fa

# Default alignment.
bio align GATTACA GATCA > gattaca1.txt

# Default alignment.
bio align GATTACA GATCA --global > gattaca2.txt

# Default alignment.
bio align GATTACA GATCA --local > gattaca3.txt

# Running variants.
bio align GATTACA GATCA --vcf > gattaca.vcf

# Running variants.
bio align GATTACA GATCA --diff  > gattaca.diff

# Running on FASTA files.
bio align align_input.fa --vcf > align_input.vcf

# Format to pairwise
bio format mafft.fa > mafft.txt

# Format to VCF
bio format mafft.fa --vcf > mafft.vcf

# Format to diff
bio format mafft.fa --diff > mafft.diff

# Select S proteins
bio fasta --gene S --protein  genomes.gb > s.fa

# Align proteins.
bio align s.fa > align-s-pairwise.txt

# Alignment as a table.
bio align s.fa --table > align-s-table.txt

# Align as variants.
bio align s.fa --vcf > align-s.vcf

# Convert genbank files to GFF
bio gff genomes.gb > genomes.gff

# Convert genbank files to GFF
bio gff genomes.gb --type CDS > CDS.gff

# Slice the GFF file.
bio gff -s 300 -e 10k genomes.gb > slice.gff

# Taxonomy listing.
bio taxon 117565 -d 5 > taxonomy.txt

# Taxonomy lineage. from file TODO
# bio taxon genomes.gb --lineage > lineage.txt

# Getting some metadata for taxon 11138 (Murine hepatitis virus)
bio meta 11138 -H > meta.txt

# Define exact SO term
bio explain exon > so.txt

# Define exact SO term
bio explain food vacuole > go.txt

# Search for terms
bio explain neutral > search.txt

# Running comm.py
comm.py file1.txt file2.txt > comm0.txt
comm.py -1 file1.txt file2.txt > comm1.txt
comm.py -2 file1.txt file2.txt > comm2.txt

# Running uniq.py
cat file1.txt file2.txt | uniq.py -d ',' > uniq0.txt
cat file1.txt file2.txt | uniq.py -f 2 -d ',' > uniq1.txt
cat file1.txt file2.txt | uniq.py -c -f 2 -d ',' > uniq3.txt

# Get data from SRA (can be spotty)
bio fetch SRR1972976 > srr.txt

# Get bioproject information
bio fetch PRJNA257197 --limit 1 > prjn.txt

# Access a transcript from ensembl.
bio fetch ENST00000288602  > enst.txt
