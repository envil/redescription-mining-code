.. _formats:

***********
Formats
***********

.. _data_formats:

Data formats
=============

.. note::
   For redescription mining, one considers entities discribed by variables divided into two sets, hereafter arbitrarily called left-hand side and right-hand side.
   This can be seen as a pair of data matrices, where entities are identified with rows and variables with columns. Both sets of variables describe the same entities, hence, the matrices have the same number of rows.
   
   If you provide the same dataset for the left and right hand sides, this will be interpreted as a settings with a single datasets, where variables can appear on either side of redescriptions, but not both in the same redescription.
   Variables can be selectively disabled on either side, to prevent them from being used in either query.
   
In *Siren*, data include:
   
* **Variables**: The variables describing the entities are divided in two sets. They can be of three types: 

  1. Boolean,
  2. categorical,
  3. or real-valued. 

Obviously, this is required.

* **Entities names**: Optional additional information, providing names for the entities.
* **Variable names**: Optional additional information, providing names for the variables.
* **Coordinates**: Optional location information, i.e. geographic coordinates of the entities. This makes the data geospatial.

Data can be imported to *Siren* via the interface menu :menuselection:`File --> Import --> Import Data`. Below, we present the data formats supported by *Siren*.

Data can be imported into *Siren* as CSV files. The program expects a pair of files, one for either side in `character-separated values <http://tools.ietf.org/html/rfc4180>`_, as can be imported and exported to and from spreadsheet programms, for instance.

There are two main formats, 

* **Full**: standard table format, or
* **Sparse**: compact format for dataset with few non-zeros entries.

The two data files need not be in the same format.

If entities names and/or coordinates are provided, they will be used to match entities across the two sides. 
Otherwise, rows will be match in order and an error will occur if the two side do not contain the same number of rows.

.. _data_csv_full:

Full format
------------

The data is stored as a table with one column for each variable and one row each entity.
The first row can contain the names of the variables.
The entities names can be included as columns named *id*. Similarly the coordinates can be included as a pair of columns named *longitude* and *latitude*, respectively.  


.. _data_csv_sparse:

Sparse format
--------------

This format allows to store data that contains few non-zero entries more compactly, as in the Matlab sparse format (or like the edge list of a bipartite graph).

Each line contains an entry of the data as a triple (entity, variable, value). This way, the data is stored as in three columns and as many rows as there are entries.
In this case the first line of the data file must contains *id*, *cid* and *value*, indicating the three columns containing the enities, variables and corresponding value, respectively.
Coordinates can be provided in a similar way under the variable names *longitude* and *latitude*.

Variable names can be provided inline, that is, simply by using the name of the variable for each entry involving it.
Alternatively, variable names can be specified separately with a special "-1" entity.
Similarly, entity names can be provided inline or separatly with a special "-1" variable.
For example, the following five lines

.. code:: bash 
	  
	  id; cid; value
	  Espoo; population; 260981
	  Helsinki; population; 614074
	  Tampere; population; 220609
	  Turku; population; 182281
	  
are equivalent to the following:

.. code:: bash
 
	  id; cid; value
	  20; -1; Espoo
	  7; -1; Tampere
	  2; -1; Turku
	  13; -1; Helsinki
	  -1; 3; population
	  2; 3; 182281
	  7; 3; 220609
	  13; 3; 614074
	  20; 3; 260981


Finally, in case of fully Boolean data without coordinates, the value can be left out. Each pair of (entity, variable) appearing is considered as True, the rest as False.

For both full and sparse formats a mention of type can be append to the first row, in such case all variable will be parse to the given type. 
For instance, in the example above the first line would be turned to ``id; cid; value; type=N`` to ensure that all variables, including population are interpreted as numerical (N) variables. Respectively B and C can be used to ensure that all variables are Boolean and categorical, respectively.

This can be useful when handling a dataset of numerical variables where some contains only two distinct values and might otherwise be interpreted as Boolean variables. It can also be a handy way to turn a dataset to fully Boolean based on zero/non-zero values. However, be warned that this can cause some troubles... 

.. _red_formats:

Redescriptions formats
========================

.. note::
   The product of redescription mining is a list of redescriptions. A redescription consist of a pair of queries over the variables describing the entities, one query for each set. The two sets of variables are arbitrarily called left-hand side and right-hand side, and so are the corresponding queries.

.. _supports:

Supports
----------

The support of a query is the set of entities for which the query holds. Any given redescription partitions the entities into four sets (In the absence of missing entries):

* E\ :sub:`10` is the set of rows for which only the left hand side query holds,
* E\ :sub:`01` is the set of rows for which only the right hand side query holds,
* E\ :sub:`11` is the set of rows for which both queries hold,
* and E\ :sub:`00` is the set of rows for which neither of the queries hold.


Redescriptions can be imported to *Siren* via the interface menu :menuselection:`File --> Import --> Import Redescriptions`. More importantly, they can be exported via the interface menu :menuselection:`File --> Export Redescriptions` and the contextual menu for a list of redescription. Below, we present the redescription formats supported by *Siren*.

.. _queries:

Queries
----------

A query is formed by combining literal using Boolean operators.


While *ReReMi* only generate linearly parsable query (see references for more details), *Siren* can actually evaluates arbitrary queries, as long as they are well formed following the informal grammar below.
In particular, parenthesis should be used to separated conjunctive blocks and disjunctive block, alternating between operators.
For example, while the later cannot be generated by *ReReMi*, :math:`(a \land{} b) \lor{} \lnot{} c` and :math:`(a \land{} b) \lor{} (c \land{} d)` are both supported. :math:`(a \land{} b) \land{} (c \land{} d)` is not, because of incorrect alternance of operators between parenthesis blocks. It should simply be written as :math:`a \land{} b \land{} c \land{} d`.

We consider three types of literals, defined over a Boolean, categorical or numerical variable respectively.

Below is an unformal grammar of *Siren*'s query language. The actual grammar can be found in the ``redquery.ebnf`` file in the ``siren.reremi`` source repertory.

.. tip::
   | query = disjunction | conjunction | literal ;
   | conjunction = conj_item { ( "&" | :math:`"\land"` ) conj_item }+ ;
   | disjunction = disj_item { ( "|" | :math:`"\lor"` ) disj_item }+ ;
   | conj_item = literal | ( "(" disjunction ")" ) ;
   | disj_item = literal | ( "(" conjunction ")" ) ;
   | literal = categorical_literal | realvalued_literal | boolean_literal ;
   | categorical_literal = ( "[" )? variable_name ( :math:`"="` | :math:`"\neq"` | :math:`"\in"` | :math:`"\in"` ) category ( "]" )?  ;
   | realvalued_literal = [ neg ] ( "[" )? [ variable_value lth ] variable_name lth variable_value ( "]" )? ; 
   | realvalued_literal = [ neg ] ( "[" )? variable_value lth variable_name ( "]" )? ; 
   | boolean_literal = [ neg ] ( "[" )? variable_name ( "]" )? ;
   | variable_name = STRING | ?/v\d+/? ;
   | category = STRING | ?/\d+/? ;
   | variable_value =  ?/[+-]?\d+([.])?\d*([Ee][-+]\d+)?/? ;
   | lth = "<" | :math:`"\leq"` ;
   | neg = "!" | :math:`"\lnot"` ;

Naturally, the type of literal and the type of variable should match, i.e., :math:`[4.0 \leq{} Va \leq{} 8.32]` is a valid numerical literal only if the corresponding variable :math:`Va` is a numerical variable. Furthermore, the upper bound of a numerical variable should always be greater or equal to the lower bound and either of them should be specified.

.. _statistics:

Redescription statistics
--------------------------

The statistics of a redescription include:

* accuracy, as measured by Jaccard coefficient :math:`|E_{11}| / (|E_{10}|+|E_{11}|+|E_{01}|)`,
* p-value,
* cardinality of the :ref:`support sets <supports>`  :math:`E_{10}`, :math:`E_{01}`, :math:`E_{11}`, :math:`E_{00}` (sometimes also referred to as alpha, beta, gamma and delta, respectively).

.. _export:

Exporting Redescriptions
-------------------------

Redescriptions from the ``Redescriptions`` tab can be exported to a file, one redescription per line, with both queries and basic statistics tab separated. Three of formatting options are available, determined by the provided filename:

* **named**: Uses the names of the variables instead of variable ids in the queries. Activated if the filename matches the pattern ``*[^a-zA-Z0-9]named[^a-zA-Z0-9]*``.
* **all** By default disabled redescriptions will not be printed when exporting redescriptions. If the filename matches the pattern ``*[^a-zA-Z0-9]all[^a-zA-Z0-9]*``, disabled redescriptions will also be printed. 
* **tex** Rather than tab separated format, if the filename as ``.tex`` extension, a tex file is produced that can be compiled to obtain a table of the redescriptions. Three table layouts are available, where the information for each redescription is listed respectively on one, two or three rows, if the filename matches the pattern ``*[^a-zA-Z0-9][1-3].[a-z]*$``. Note that this format cannot be imported back.

Inside a siren package, the redescriptions are stored in tab separated format.

The fields included when exporting redescriptions and when displaying them in the interface can be set via the :menuselection:`File --> Fields setup` menu entries.

.. _import:

Importing Redescriptions
-------------------------

Tab separated formats can be imported into *Siren*, *TeX* cannot.
