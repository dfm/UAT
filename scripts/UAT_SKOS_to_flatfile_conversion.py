# coding: utf-8

from datetime import datetime
import cStringIO
import rdflib
import pandas as pd

#assign this variable to the name of the exported UAT SKOS-RDF file, found in the same location as this script.
rdf = "export_skos-xl_15092014111447.rdf"

print "Reading the SKOS file...this may take a few seconds."
#reads the SKOS-RDF file into a RDFlib graph for use in this script
g = rdflib.Graph()
result = g.parse((rdf).encode('utf8'))

#defines certain properties within the SKOS-RDF file
litForm = rdflib.term.URIRef('http://www.w3.org/2008/05/skos-xl#literalForm')
prefLabel = rdflib.term.URIRef('http://www.w3.org/2008/05/skos-xl#prefLabel')
TopConcept = rdflib.term.URIRef('http://www.w3.org/2004/02/skos/core#topConceptOf')
broader = rdflib.term.URIRef('http://www.w3.org/2004/02/skos/core#broader')
Concept = rdflib.term.URIRef('http://www.w3.org/2004/02/skos/core#Concept')
vocstatus = rdflib.term.URIRef('http://art.uniroma2.it/ontologies/vocbench#hasStatus')

#a list of all top concepts
alltopconcepts = [bv for bv in g.subjects(predicate=TopConcept)]
#list of all concepts
allconcepts = [gm for gm in g.subjects(rdflib.RDF.type, Concept)]

#find all terms that have the given term listed as a broader term, so they are therefore narrower terms
def getnarrowerterms(term):
    narrowerterms = {}
    terminal = rdflib.term.URIRef(term)
    try:
        for nts in g.subjects(predicate=broader, object=terminal):
            try:
                narrowerterms[terminal].append(nts)
            except KeyError:
                narrowerterms[terminal] = [nts]
        return narrowerterms[terminal]
    except KeyError:
        pass

#a function to return the status of a term
def getvocstatus(term):
    d=rdflib.term.URIRef(term)
    for vcstatus in g.objects(subject=d, predicate=vocstatus):
        return vcstatus

#a function to return the human readable form of the prefered version of a term.
def lit(term):
    d = rdflib.term.URIRef(term)
    for prefterm in g.objects(subject=d, predicate=prefLabel):
        for litterm in g.objects(subject=prefterm, predicate=litForm):
            return litterm

#get all deprecated terms into a list
deprecated = []
for term in allconcepts:
    termstats = getvocstatus(term)
    if termstats == "Deprecated":
        deprecated.append(lit(term))   

#a function to travel all the way down each path in the thesarus and return this information into a list.
#a function to travel all the way down each path in the thesarus and return this information into a list.
def descend(term, parents, out_list):
    lvln = getnarrowerterms(term)
    if lvln != None: #if there are narrower terms...
        for z in lvln:
            children = parents[:]
            #w = lit(z)
            #print lit(term)
            if lit(z) in deprecated:
                children = parents[:]
                children.append(lit(term))
                if children not in out_list:
                    out_list.append(children)
            else:
                children.append(lit(term))
                if children not in out_list:
                    out_list.append(children)
                descend(z, children, GLOBAL_OUT_LIST)
    else: #if there are no more narrower terms...
        children = parents[:]
        children.append(lit(term))
        if children not in out_list:
            out_list.append(children)

print "Organizing the terms, almost finished."
#runs the functions across all terms and outputs to pandas dataframe.
timestamp = datetime.now().strftime("_%Y_%m%d_%H%M%S")
GLOBAL_OUT_LIST = []
out_list = []
for term in alltopconcepts:
    descend(term, [],GLOBAL_OUT_LIST)
out_df = pd.DataFrame.from_dict(GLOBAL_OUT_LIST)

#counts the number of columns in the data frame and creates the header row.
numofcol = len(out_df.columns)
colnames = []
for i in range(1,numofcol+1):
    col = 'level '+str(i)
    colnames.append(col)
out_df.columns = [colnames]

#sorts the resulting csv file alphabetically
out_df_final = out_df.sort(colnames)

#utf-8-sig encoding fixs umlauts, etc, in the output csv.
out_df_final.to_csv('UAT_flatfile{}.csv'.format(timestamp), encoding='utf-8-sig',index=False)

print "Finished. See UAT_flatfile"+timestamp+".csv"