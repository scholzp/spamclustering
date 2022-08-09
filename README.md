# Installation
Running pip with `requierements.txt` should be enough to use these scripts. 

It is adviced to create a [virtuell python environment](https://docs.python.org/3/library/venv.html).

# Documentation
Documentation is located at `docs/`. Prebuild HTML documatation is available at `docs/build/html`. Building documatation in other document fomats is supported, see `Building documentation`.

## Building documentation
Documentation is build and managed thorugh the help of [Sphinx](https://www.sphinx-doc.org/en/master/). See sphinx documentation for more help. Running `requierements.txt` will install Sphinx. Sphinx has different [builders](https://www.sphinx-doc.org/en/master/man/sphinx-build.html) available by default. For html build, simply execute

    make html

in `docs/`. To do this, `make` should be installed on the system.

If creater changes were done to the package structure, the respcecitve `.rst` files need to be generated new. These reside in `docs/source`. Old `.rst` files will be overwritten in this processs. If you don't want this to happen, remove the `-f` flag. The follwing command needs to be executed from within `docs` to recreate `*rst` files for each module/package:

    sphinx-apidoc -f -o ./source ../spamclustering

After recreating `.rst` files, cleaning the build dir is a good idea:

    make clean


# Running example scripts
Examples on how to use this code can be found in `spamclustering` prefix with `example_`. All example scripts must be run from root directory.

## MBoxReader
The MBox Reader reads a file in `MBox` format and extracts the respective `eml` files. These files are then stored at `<path_to_output_dir>`.

    python -m spamclustering.example_mboxReader -i <path_to_mbox>/file.mbox -o <path_to_output_dir>

## Anonymizing emails
The example script will take a directory or single file as input argument via `<path_to_dir1>`. After performing the necessary anonymization steps, the resulting `eml` files will be written to `<path_to_result>`. Optional arguments are a list of domains to block and a flag, which controls if the error log is written to a file. If both present, the `block list` must be the third argument. `block list` can be omitted, but this might produce errors. The log flag is either `True` or `False`, while `False` is the default value. Setting `log=True` will result in a text file named `error_log.txt` located at `<path_to_result>`.

    python -m spamclustering.example_anonimzer <path_to_dir1> <path_to_result> test/domains.txt log=True


## Diff of directories
Compare both given directories and tries to find matches betweeen clusters (e.g. subdirectories of the given directories). These matches are later compared and diffs between the gold standard and the directory to compare are listed on directory basis.

    python -m spamclustering.example_difftool <path_gold_standard> <path_to_compare>

## Algorithms
### Context triggered piecewise hash (CTPH)
Performs clustering with the help of a context triggered piecewise hash function. Files found in `<path_to_files>` are processed, similar files are grouped in a cluster and the cluster is then written to `path_to_cluster_out`. 

    python -m spamclustering.example_ctph <path_to_files> <path_to_cluster_out>