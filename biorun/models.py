"""
This package attempts to simplify the BioPython SeqRecords into a simpler, flatter structure that
can be more readily worked with.
"""
import sys, os, json
from biorun import utils
from collections import OrderedDict

from itertools import *
from pprint import pprint

from biorun.const import *

try:
    from Bio import SeqIO
    from Bio.Seq import Seq
    from Bio.SeqRecord import SeqRecord
    from Bio.SeqFeature import Reference, CompoundLocation, FeatureLocation
except ImportError as exc:
    print(f"*** {exc}", file=sys.stderr)
    print(f"*** This software requires biopython.", file=sys.stderr)
    print(f"*** Try: conda install biopython", file=sys.stderr)
    sys.exit(1)

logger = utils.logger


def get_feature_id(feat):
    """
    Attempts to generate a meaningful name for a feature
    """
    name = utils.first(feat.qualifiers.get_data("gene", '')) or feat.type

    return name


def get_feature_decription(feat):
    """
    Attempts to generate a meaningful name for a feature
    """
    synon = utils.first(feat.qualifiers.get_data("gene_synonym", ''))

    db_xref = utils.first(feat.qualifiers.get_data("db_xref", ''))

    desc = f"type={feat.type} loc={feat.location}"

    if synon:
        desc = f"{desc} synonym={synon}"

    if db_xref:
        desc = f"{desc} db_xref={db_xref}"

    return desc


def has_feature(item, name="gene"):
    """
    A filtering function to checks if a record contains keys with a name.
    """
    return item.get(name, [''])[0]


def filter_features(items, start=0, end=None, gene=None, ftype=None, regexp=None):
    # Filter by type.
    if ftype and ftype != "all":
        items = filter(lambda f: f.get('type') == ftype, items)

    # Filter by name.
    if gene:
        items = filter(lambda f: gene in f.get("gene", []), items)

    # Filter by start.
    if start:
        items = filter(lambda f: start <= f.get('start'), items)

    # Filter by end.
    if end:
        items = filter(lambda f: f.get('end') <= end, items)

    # Filters by matching a regular expression
    if regexp :
        items = filter(lambda f: regexp.search(str(f)), items)

    return items


def first(item, key, default=""):
    "Shortcut to obtain the first element of the list"
    return item.get(key, [default])[0]


def rec_name(f):
    """
    Creates a record name from a JSON feature.
    """
    gene = first(f, "gene", )
    protein_id = first(f, "protein_id") or "None"
    name = f"{gene}|{protein_id}"
    return name


def rec_desc(f):
    """
    Creates a record description from JSON feature.
    """
    ftype = f.get("type", ".")
    db_xref = first(f, 'db_xref')
    desc = f"{ftype} {db_xref}"

    return desc


def get_translation_records(item, param):
    """
    Produces SeqRecods for each feature that have translations.
    """

    # All features for the item
    feats = item[FEATURES]

    # Filtering function for translations.
    has_translation = lambda f: f.get('translation', [''])[0]

    # Features with translation.
    feats = filter(has_translation, feats)

    # Additional filters
    feats = filter_features(feats, gene=param.gene, ftype=param.type)

    # Hoist the variables out.
    start, end = param.start, param.end

    # Produce the translation records.
    for f in feats:
        # Fetch the translation.
        trans = first(f, "translation")[start:end]

        # Set up the metadata.
        name = rec_name(f)
        desc = rec_desc(f)

        # Generate sequence record.
        rec = SeqRecord(Seq(trans), id=name, description=desc)

        yield rec


def get_feature_records(data, param):
    """
    Returns records from a list of GenBank
    """

    feats = data[FEATURES]
    origin = data[ORIGIN]
    feats = filter_features(feats, gene=param.gene, ftype=param.type)

    # Ignore translation warnings
    if param.translate:
        import warnings
        from Bio import BiopythonWarning
        warnings.simplefilter('ignore', BiopythonWarning)

    start, end = param.start, param.end

    for f in feats:
        name = rec_name(f)
        desc = rec_desc(f)
        locations = f.get("location", [])

        dna = Seq('')
        for x_start, x_end, strand in locations:
            sub = Seq(origin[x_start - 1:x_end])
            if strand == -1:
                sub = sub.reverse_complement()
            dna += sub

        seq = dna.translate()[:-1] if param.translate else dna

        seq = seq[start:end]

        rec = SeqRecord(seq, id=name, description=desc)

        # Sanity check for translation
        if param.translate:
            expected = first(f, "translation")[start:end]
            observed = str(rec.seq)
            if expected and expected != observed:
                rec.description = f"{rec.description} (possible translation error)"

        yield rec

def serialize(value):
    """
    Serializes values to JSON ready type.
    """

    # The type of of the incoming value.
    curr_type = type(value)

    # Reference types will be dictionaries.
    if curr_type == Reference:
        return dict(title=value.title, authors=value.authors, journal=value.journal, pubmed_id=value.pubmed_id)

    # Serialize each element of the list.
    if curr_type == list:
        return [serialize(x) for x in value]

    # Serialize the elements of an Ordered dictionary.
    if curr_type == OrderedDict:
        return dict((k, serialize(v)) for (k, v) in value.items())

    return value


def get_origin(item, param):
    """
    Returns the origin sequence from an JSON item
    """
    # Prints the source sequence
    seq = item[ORIGIN][param.start:param.end]
    desc = item[DEFINITION]
    seqid = item[SEQID]
    locus = item[LOCUS]
    seqid = param.seqid or seqid
    rec = SeqRecord(Seq(seq), id=seqid, name=locus, description=desc)
    return rec


def convert_genbank(stream):
    """
    Converts a stream to a GenBank file into json.
    """

    # Parses the genbank into memory.
    recs = parse_genbank(stream)

    # The outer dictionary containing multiple records.
    data = []

    # Add each record separately.
    for rec in recs:

        # The individual SeqRecords as dictionaries.
        item = dict()

        # Fill the standard SeqRecord fields.
        item[SEQID] = rec.id
        item[DEFINITION] = rec.description
        item[DBLINK] = rec.dbxrefs
        item[LOCUS] = rec.name

        # Fill in all annotations.
        for key, value in rec.annotations.items():
            item[key] = serialize(value)

        # Fill in the features.
        feats = []
        for feat in rec.features:
            ftype = feat.type
            start = int(feat.location.start) + 1
            end = int(feat.location.end)

            oper = feat.location_operator

            # print (feat.location, type(feat.location))
            location = [(loc.start + 1, loc.end, loc.strand) for loc in feat.location.parts]
            elem = dict(start=start, end=end, type=ftype, location=location, operator=oper)

            for (k, v) in feat.qualifiers.items():
                elem[k] = serialize(v)

            feats.append(elem)

        # Add the features
        item[FEATURES] = feats

        # Save the sequence as well
        item[ORIGIN] = str(rec.seq)

        # Each item keyed as the record.id.
        data.append(item)

        # pprint(rec.annotations)

        # print(rec)

    return data


def parse_genbank(stream, fmt=utils.GENBANK):
    """
    Parses GenBank into sequence records.
    """
    recs = SeqIO.parse(stream, format=fmt)
    return recs


if __name__ == "__main__":
    import doctest

    doctest.testmod()
