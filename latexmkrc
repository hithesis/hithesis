# vim: set ft=perl:
@default_files = ('hithesis.dtx');

$pdf_mode = 1;
$bibtex_use = 2;
$recorder = 1;
$preview_continuous_mode = 1;
$clean_ext = "synctex.gz acn acr alg aux bbl bcf blg brf fdb_latexmk glg glo gls idx ilg ind lof log lot out run.xml toc pdf thm toe ist idx";
$pdflatex = "xelatex -file-line-error -halt-on-error -src-specials -synctex=1 %O %S";
$pdf_update_method = 0;

$makeindex = 'makeindex -s gind.ist %O -o %D %S';

# Show CPU time used.
$show_time = 1;

# Process glossary (change history).
add_cus_dep('glo', 'gls', 0, 'makeglo2gls');

sub makeglo2gls {
    system("makeindex -s gglo.ist -o \"$_[0].gls\" 
        -t \"$_[0].glg\" \"$_[0].glo\"");
}

