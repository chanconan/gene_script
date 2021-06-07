import apybiomart as abiomart
import requests
import json
import csv

# from pybiomart import Dataset

# print(abiomart.find_marts())

# hsapiens_attr = abiomart.find_attributes(dataset="hsapiens_gene_ensembl")
# print(hsapiens_attr)

# dataset = abiomart.query(attributes=["ensembl_gene_id", "external_gene_name","uniprot_gn_symbol","uniprot_gn_id"],
#       filters = {"chromosome_name":"1"})
# # print(dataset)
# print(dataset.loc[dataset['Gene name']=="ADAT2"])


# dataset = Dataset(name='hsapiens_gene_ensembl',
#                   host='http://www.ensembl.org')
# print(dataset)

# # dataset.query(attributes=['ensembl_gene_id', 'external_gene_name'],
# #               filters={'chromosome_name': ['1','2']})

class EnsemblGene:
    base_url = "http://rest.ensembl.org"

    def get_gene_details(self, genes: list):
        gene_props = { "genes" : []}
        for gene in genes:
            gene_obj = {'Gene Name': gene}
            ensembl_id = self.get_ensembl_id(gene)
            canonical_transcript = self.get_ensembl_transcript(ensembl_id)
            ccds_id = self.get_ccds_id(ensembl_id, canonical_transcript)
            refseq_match_id = self.get_refseq_match(canonical_transcript)
            uniprot_id = self.get_uniprot_id(canonical_transcript)
            gene_obj['Ensembl ID'] = ensembl_id
            gene_obj['CCDS ID'] = ccds_id
            gene_obj['Uniprot ID'] = uniprot_id
            gene_obj['RefSeq Match'] = refseq_match_id
            gene_props["genes"].append(gene_obj)
        return gene_props

    def get_ensembl_id(self, gene: str):
        extended_uri = "/xrefs/symbol/homo_sapiens/" + gene + "?content-type=application/json&expand=1"
        response = requests.get(self.base_url + extended_uri)
        return response.json()[0]['id']

    def get_ccds_id(self, ensembl_id, transcript_id):
        extended_uri = "/overlap/id/" + ensembl_id
        params = {
            'content-type': 'application/json',
            'feature': 'transcript',
            'biotype': 'protein_coding',
            'expand': '1'
        }
        response = requests.get(self.base_url + extended_uri, params = params)
        for transcript in response.json():
            if transcript['id'] == transcript_id and transcript.get('ccdsid') != None:
                return transcript['ccdsid'].split('.')[0]
        return None
        
    def get_refseq_match(self, transcript_id):
        extended_uri = "/xrefs/id/" + transcript_id
        params = {'content-type':'application/json'}
        response = requests.get(self.base_url + extended_uri, params = params)
        for item in response.json():
            if item.get('ensembl_identity') != None and item['ensembl_identity'] == 100 and item['dbname'] == 'RefSeq_mRNA' and item['xref_identity'] == 100:
                return item['display_id']
        return None

    def get_ensembl_transcript(self, ensembl_id):
        extended_uri = "/lookup/id/" + ensembl_id
        params = {
            'expand': '1'
        }
        response = requests.get(self.base_url + extended_uri, params = params, headers = {'Content-Type': 'application/json'})
        for transcript in response.json()['Transcript']:
            if transcript['is_canonical'] == 1:
                return transcript['id']
        return None

    def get_uniprot_id(self, transcript_id):
        url = 'http://www.uniprot.org/uploadlists/'
        params = {
            'from': 'ENSEMBL_TRS_ID',
            'to': 'ACC',
            'format': 'tab',
            'query': transcript_id
        }
        response = requests.get(url, params = params, headers = {
            "Content-Type": "application/json"
        })
        return response.text.split('\t')[-1].split('\n')[0]


print("Enter/Paste your content.")
contents = []
line = input("Type exit when complete\n")
while line != 'exit':
    try:
        line = input()
    except EOFError:
        break
    if line != 'exit':
        contents.append(line)

ensemblGene = EnsemblGene()

gene_data = ensemblGene.get_gene_details(contents)['genes']
csv_file = open('gene_data.csv', 'w')
csv_writer = csv.writer(csv_file)
 
# Counter variable used for writing
# headers to the CSV file
count = 0
for gene in gene_data:
    if count == 0:
 
        # Writing headers of CSV file
        header = gene.keys()
        csv_writer.writerow(header)
        count += 1
 
    # Writing data of CSV file
    csv_writer.writerow(gene.values())
csv_file.close()