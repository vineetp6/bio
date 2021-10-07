"""
The main job runner. Register additional functions here.
"""

import importlib
import logging
import sys

import biorun.libs.placlib as plac
from biorun import utils

# Module level logger
logger = utils.logger

from biorun import VERSION

#
# Subcommand registration:
#
# name = (module.function, help_flag, listing_flag, command_help)
#
SUB_COMMANDS = dict(
    search=("biorun.search.run", True, False, "search for information"),
    fetch=("biorun.fetch.run", True, True, "download GenBank/ENSEMBL data"),
    fasta=("biorun.fasta.run", True, True, "convert to FASTA"),
    gff=("biorun.gff.run", True, True,"convert to GFF"),
    align=("biorun.align.run", True,True, "align sequences"),
    format=("biorun.format.run", True, True,"reformat aligned fasta"),
    taxon=("biorun.taxon.run", False, True,"operate on NCBI taxonomies"),
    explain=("biorun.ontology.run", False, True,"explain biological terms"),
    meta=("biorun.meta.run", False, True,"download metadata by taxonomy ID"),
    mygene=("biorun.mygene.run", False, True,"connect to mygene interface"),
    comm=("biorun.comm.run", False, False, "find common elements"),
    uniq=("biorun.uniq.run", False, False, "find unique elements"),
)


DOWNLOAD_CMD = '--download'

# Generates indented help for each subcommand
block = [f"  bio {key:9} : {value[3]}" for (key, value) in SUB_COMMANDS.items() if value[2]]

# Join help into a section.
block = "\n".join(block)

# Fill help section into the usage.
USAGE = f"""
bio: making bioinformatics fun again 

{block}

Examples:

  bio fetch NC_045512 MN996532 > genomes.gb
  bio fasta genomes.gb --gene S | bio align
  bio gff genomes.gb --type CDS
  bio taxon 2697049 --lineage
  bio align GATTACA GATCA  
  bio explain exon 
  bio mygene HAD3 -fields refseq
 
See also: https://www.bioinfo.help

Version: {VERSION}
"""


def fix_parameter(value):
    """
    Allows more error tolerant parameter input (mistakenly using shortform for longform and viceversa)

    Remaps -start to --start, --F to -F
    """

    # If it looks like a valid number we don't alter it.
    try:
        float(value)
        return value
    except ValueError as exc:
        pass

    # Detect longform parameters
    twodash = value.startswith("--")

    # Detect shortform parameters.
    onedash = value.startswith("-") and not twodash

    # Detect if value is single letter
    oneletter = len(value.strip("-")) == 1

    # Single letter but two dashes. Drop a leading dash.
    if twodash and oneletter:
        value = value[1:]

    # One dash but more more than one letter. Add a dash.
    if onedash and not oneletter:
        value = f"-{value}"

    return value


def interrupt(func):
    """
    Intercept keyboard interrupts.
    """

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            sys.exit(0)

    return wrapper


@interrupt
def router():
    """
    Route the tasks based on subcommands parameters.
    """

    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        # Run a test
        from biorun import test
        test.main()
        sys.exit(0)

    # More verbose messages
    debug_flag = "--debug"
    if debug_flag in sys.argv:
        sys.argv.remove(debug_flag)
        utils.logger = utils.apply_debug_logger()
        logger.debug("verbose messages on")

    # Print usage when no parameters are passed.
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    # Trigger the download if needed
    if DOWNLOAD_CMD in sys.argv:
        utils.download_prebuilt()
        sys.exit()

    # Lowercase the subcommand.
    sys.argv[1] = sys.argv[1].lower()

    # Check the subcommand.
    cmd = sys.argv[1]

    # Raise an error is not a valid subcommand.
    if cmd not in SUB_COMMANDS:
        print(USAGE, file=sys.stderr)
        logger.error(f"invalid command: {cmd}")
        sys.exit(-1)

    # Remove the command from the list.
    sys.argv.remove(cmd)

    # Allow multiple forms of parameters to be used.
    sys.argv = list(map(fix_parameter, sys.argv))

    # Delegate to the imported method
    modfunc, flag, tmp, help = SUB_COMMANDS[cmd]

    # Add the help flag if no other information is present beyond command.
    if sys.stdin.isatty() and flag and len(sys.argv) == 1:
        sys.argv.append("-h")

    # Format: module.function
    mod_name, func_name = modfunc.rsplit(".", maxsplit=1)

    # Dynamic imports to allow other functionality
    # to work even when required for certain subcommands may be missing.
    mod = importlib.import_module(mod_name)

    # Get the function of the module
    func = getattr(mod, func_name)


    # Execute the function with plac.
    plac.call(func)


if __name__ == '__main__':
    router()
