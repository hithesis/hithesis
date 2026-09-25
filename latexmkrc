# vim: set ft=perl:
@default_files = ('src/hithesis.dtx');

$pdf_mode = 1;
$bibtex_use = 2;

# 成果页的条目走自己的一次 bibtex：模板把 \bibstyle、\bibdata 与点名的
# \citation 写进 <jobname>-pub.aux（见 hit-thesis-backmatter.dtx 的 publication
# 环境），这里跟着主 bibtex 之后跑一次，产出 <jobname>-pub.bbl。没有那份 aux
# 就什么都不做，不用成果页的文档一切照旧。
$bibtex = 'internal hit_pub_bibtex';
sub hit_pub_bibtex {
   my $ret = system( "bibtex", $$Psource );
   my $pub = $$Psource;
   $pub =~ s/\.aux$//;
   $pub .= "-pub";
   if ( -e "$pub.aux" ) { system( "bibtex", $pub ); }
   return $ret;
}
$recorder = 1;
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

