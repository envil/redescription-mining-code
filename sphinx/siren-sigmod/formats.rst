.. _formats:

*************
Data Formats
*************

In *Siren*, data include:
   
* **Variables**: The variables describing the entities are divided in two sets. They can be of three types: 

  1. Boolean,
  2. categorical,
  3. or real-valued. 

Obviously, this is required.

* **Entities names**: Optional additional information, providing names for the entities.
* **Variable names**: Optional additional information, providing names for the variables.
* **Coordinates**: Optional location information, i.e. geographic coordinates of the entities. This makes the data geospatial.

Data can be imported to *Siren* via the interface menu :menuselection:`File --> Import --> Import Data`. 

Data can be imported into *Siren* as CSV files. The program expects a pair of files, one for either side in `character-separated values <http://tools.ietf.org/html/rfc4180>`_, as can be imported and exported to and from spreadsheet programms, for instance.

In particular, the data can stored as a table with one column for each variable and one row each entity.
The first row can contain the names of the variables.
The entities names can be included as columns named *ids*. Similarly the coordinates can be included as a pair of columns named *longitudes* and *latitudes*, respectively.  
