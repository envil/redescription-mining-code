.. _funct:

***************
Functionalities
***************

.. note::
   Using *Siren*, a user can explore data of his interest by interactively mining, visualizing and editing redescriptions.

   The main functionalities of *Siren* can be categorized into mining, visualizing and editing.

.. _func_mine:

Mining
======================================

At the core of *Siren* is the *ReReMi* redescription
mining algorithm. Various modes of interaction with the mining
algorithm are possible through the interface.

* Mine redescriptions from the data automatically.  
* Mine extensions of an existing redescription, on both sides or selectively on one side.
* It is possible to select a subset of variables for use in mining/expanding, by disabling some variables and to specify a subset of entities of interest to emphasize.

.. image:: _static/stories/mine/mine.gif
	   :alt: Siren in action		 

.. _func_viz:

Vizualizing
======================================

*Siren* offers a number of different visualizations.

.. _viz_paco:

Parallel Coordinates
---------------------

A *parallel coordinates* plot represents the values taken by the entites for the variable appearing in the queries. It allows to easily visualize the impact of the queries conditions on the support of the redescription.

.. image:: _static/screenshots/PacoView.png

.. _viz_proj:

Projections
---------------------

The *axis projection* and a number of data projections from the `scikit-learn package <http://scikit-learn.org/>`_ allow to highlight different aspects of the data.

* The *Axis Projection* plots the values of two selected variables.
* `Isomap Embedding <http://scikit-learn.org/0.13/modules/generated/sklearn.manifold.Isomap.html#sklearn.manifold.Isomap>`_
* `Locally Linear Embedding <http://scikit-learn.org/0.13/modules/generated/sklearn.manifold.LocallyLinearEmbedding.html#sklearn.manifold.LocallyLinearEmbedding>`_
* `Multidimensional Scaling Embedding <http://scikit-learn.org/0.13/modules/generated/sklearn.manifold.MDS.html#sklearn.manifold.MDS>`_
* `Randomized PCA Decomposition <http://scikit-learn.org/0.13/modules/generated/sklearn.decomposition.RandomizedPCA.html#sklearn.decomposition.RandomizedPCA>`_ (discrete Karhunen–Loève transform, KLT)
* `Sparse Random Projection <http://scikit-learn.org/0.13/modules/generated/sklearn.random_projection.SparseRandomProjection.html>`_
* `Spectral Embedding <http://scikit-learn.org/0.13/modules/generated/sklearn.manifold.SpectralEmbedding.html#sklearn.manifold.SpectralEmbedding>`_ (Johnson-Lindenstrauss transform)
* `Totally Random Trees Representation <http://scikit-learn.org/0.13/modules/generated/sklearn.ensemble.RandomTreesEmbedding.html#sklearn.ensemble.RandomTreesEmbedding>`_

.. image:: _static/screenshots/MDSView.png

.. _viz_map:

Maps (for geospatial data)
---------------------------

When the entities are geographic locations, we qualify the redescriptions as geospatial.
Such redescriptions can be displayed on a map to show the locations 
where both queries hold, only the left hand side query 
holds and only the right hand side query holds.

.. image:: _static/screenshots/MapView.png

.. _func_edit:

Editing and Selecting
======================

Existing redescriptions can be edited and the visualization and statistics will be recomputed and changes reflected in the original redescription in the list and other visualizations of that same redescription.

.. image:: _static/screenshots/ViewsSide.png

It is also possible to build a new redescription from scratch.

Dragging the interval boxes in the parallel coordinates plot allows to edit the redescription interactively.

.. image:: _static/screenshots/PacoEdit.png

The user can select single entites from a view by clicking the corresponding dot/line in a view.

.. image:: _static/screenshots/SelectDot.png

Furthermore, he can select a subset of entities by drawing a enclosing polygon directly on the view.

.. image:: _static/screenshots/SelectPoly.png






