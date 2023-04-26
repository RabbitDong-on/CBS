            Cloud Bug Study DB public
            =========================

how to use CBS-public?
-----------------------

1. docs/classifications.pdf
    
    Classifications.pdf is guideline for our tags classification in
    this cloud bug study. the classification document consists of
    aspects (a-), type of bug (t-), hardware fault (hw-), hardware
    fault type (ht-), software fault (sw-), implication (i-), scale of
    issue (x-), component that involved on this bug (c-), and jira-api
    (j-). You will find those tags on each system under raw-public
    folder.

2. script-public/genhtml.py

    Genhtml.py script is helping you to filter and generate an html
    that contains the issues' table. There are six options systems
    name that can be used on this script, the systems are cassandra,
    flume, hbase, hdfs, mapreduce and zookeeper. Moreover, you can also
    filter the issue based on tags (find more available options on 
    valid-tags.txt). Here are examples to run the genhtml
    script.

    - Filter by system(s) name only.
        Command: ./genhtml.py mapreduce hbase                    
    
    - Filter by tag(s) only.
        Command: ./genhtml.py a-perf i-perf

    - Filter by system(s) and tag(s).
        Command: ./genhtml.py mapreduce a-perf i-perf
     
3. script-public/top-k.py 

    Top-k.py shows you top 100 issues and generates an html that
    contains the issues' table. You are able to put some parameter
    just like genhtml script, but top-k script also be able to filters
    the issues based on the newest issue (bynewst), oldest (byoldest),
    longest to resolve (ttr), and total comments (bycomm). Here are
    some examples to run this top-k script.

    - Show HBase with a-perf and order by the most comments. 
        Command: ./top-k hbase a-perf bycomm

    - Show all systems with a-perf and i-perf order by the newest issues.
        Command: ./top-k.py a-perf i-perf bynewest


4. raw/*.txt

    These raw files contain the issue entries and our annotations. 
    To perform more advanced analyses, you can write python scripts that
    parse these raw files. 

