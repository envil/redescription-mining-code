.. _funct:

***************
Functionalities
***************


Using *Siren*, a user can explore data of his interest by interactively mining, visualizing and editing redescriptions.

.. _func_mine:

Mining
======================================

At the core of *Siren* is the *ReReMi* redescription
mining algorithm. Various modes of interaction with the mining
algorithm are possible through the interface.

* Mine redescriptions from the data automatically.  
* Mine extensions of an existing redescription, on both sides or selectively on one side.
* It is possible to select a subset of variables for use in mining/expanding, by disabling some variables and to specify a subset of entities of interest to emphasize.

.. _func_viz:

Vizualizing
======================================

*Siren* offers a number of different visualizations.

* A *parallel coordinates* plot represents the values taken by the entites for the variable appearing in the queries. It allows to easily visualize the impact of the queries conditions on the support of the redescription.

.. image:: _static/screenshots/PacoView.png 

* A number of *data projections* from the `scikit-learn package <http://scikit-learn.org/>`_ allow to highlight different aspects of the data.

.. image:: _static/screenshots/MDSView.png

* A *map* (for geospatial data) to show the locations 
where both queries hold, only the left hand side query 
holds and only the right hand side query holds.

.. image:: _static/screenshots/MapView.png

.. _func_edit:

Editing and Selecting
======================

Existing redescriptions can be edited and the visualization and statistics will automatically recomputed.
It is also possible to build a new redescription from scratch.

.. image:: _static/screenshots/SelectPoly.png






