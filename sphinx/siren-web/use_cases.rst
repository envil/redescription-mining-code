.. _usecase:

******************
Sample Use-Cases
******************

.. _uc_bio:

Biological niche-finding
=========================

.. note:: 
   The first use-case concerns niche-finding, i.e. the problem of finding species' bioclimatic envelope, an important task in biology.

   The :ref:`video tutorial <vtutorial>` provides a step by step use-case with this data.

Data
------

The Bio data describes spatial areas of Europe, 2575 squares of side roughly 50 kilometers. The left hand side data contains information 
about the mammals that live in these areas denoted with the names of the respective species. The minimum, maximum and average monthly temperatures in degrees Celsius as well as average monthly precipitation in millimeters, make up the right hand side data, denoted as :sup:`+`\ :sub:`x`\ , t\ :sup:`-`\ :sub:`x`\ , t\ :sup:`=`\ :sub:`x`\ and p\ :sup:`=`\ :sub:`x`\ , respectively, where x is the number of the month.
The data comes from two publicly available datasets: European Mammals atlas and Worldclim climate data.

Exploration
---------------

1. The first tab contains a list of entities. Expanding columns of interest reveals the actual values of the variables.

.. image:: ../_figs/stories/BIO/windows/Bio_EntitiesClosed.png
	   :class: sideL
.. image:: ../_figs/stories/BIO/windows/Bio_EntitiesOpen.png
	   :class: sideR

2. Next comes the list of left-hand side variables and right-hand side variables.

.. image:: ../_figs/stories/BIO/windows/Bio_VariablesLHS.png
	   :class: sideL
.. image:: ../_figs/stories/BIO/windows/Bio_VariablesRHS.png
	   :class: sideR

3. Let's consider the Moose, plot this variable in a map to create a new redescription.

.. image:: ../_figs/stories/BIO/interact/Bio_VOpenRMoose.png

4. Then, we can let the algorithm find best expansions.

.. image:: ../_figs/stories/BIO/interact/Bio_ExpansionsInitRMoose.png

5. After a few seconds, we get a number of expansions and can sort them by accuracy or let the algorithm process them to select the top non-redundant ones, here we obtain one.

.. image:: ../_figs/stories/BIO/interact/Bio_ExpansionsSortedRMoose.png
	   :class: sideL
.. image:: ../_figs/stories/BIO/interact/Bio_ExpansionsFilteredRMoose.png
	   :class: sideR

6. Let's have a look at this redescription about the Moose, simultaneously plotting it in a Multidimensional Scaling projection and on a map.

.. image:: ../_figs/stories/BIO/windows/Bio_MDSViewRMoose.png
	   :class: sideL
.. image:: ../_figs/stories/BIO/windows/Bio_MapViewRMoose.png
	   :class: sideR

7. We can select a dot to highlight the entities. The views are linked together so the entity will be highlighted across all views for that specific redescription.

.. image:: ../_figs/stories/BIO/interact/Bio_SelectDotSideRMoose.png

8. To select a set of points lying in some area, we can draw an enclosing polygon. Similarly, when we click :menuselection:`Edit --> (De)select polygon` (or press the corresponding key) to select the dots inside the polygon, they will be highlighted across the different views.

.. image:: ../_figs/stories/BIO/interact/Bio_DrawPolySideRMoose.png 

.. image:: ../_figs/stories/BIO/interact/Bio_SelectPolySideRMoose.png

9. With this selected entities we can recompute the left-hand side query while adding weight on this area, to try removing it from E\ :sub:`10`. To do this, we clear the left-hand side query, press ``ENTER`` to update the redescription then choose :menuselection:`Process --> Overfit LHS`.

.. image:: ../_figs/stories/BIO/interact/Bio_OverfitInitRMoose.png 

10. And we automatically obtain a new left-hand side query involving Mountain Hare, removing this region from the support.

.. image:: ../_figs/stories/BIO/interact/Bio_OverfitResultOrgRMoose.png


.. _uc_dblp:

DBLP Computer Science Bibliography
===================================

.. note::
   In this third example, we consider non-geospatial data, namely from the DBLP Computer Science Bibliography.

Data
-----

This dataset comes from the `DBLP data base <http://www.informatik.uni-trier.de/~ley/db/>`_ of computer science bibliography.
Here the entities are researchers, the left-hand side data indicates major CS conferences in which they have published while the right-hand side data contains co-authorship information.

Unlike in the previous examples, the entities in this data are not associated to goegraphic coordinates, hence this data is not geospatial and the redescriptions cannot be plotted on maps. However, the other visualizations can be used for exploration.

Exploration
------------

1. Once more, we can consult the list of entities in the first tab.

.. image:: ../_figs/stories/DBLP/windows/DBLPPick_Entities.png

2. Similarly, left-hand side variables and right-hand side variables are listed in the next two tabs.

.. image:: ../_figs/stories/DBLP/windows/DBLPPick_VariablesLHS.png
	    :class: sideL
.. image:: ../_figs/stories/DBLP/windows/DBLPPick_VariablesRHS.png
	   :class: sideR

3. Redescriptions are listed in the fourth tab.

.. image:: ../_figs/stories/DBLP/windows/DBLPPick_Reds.png

4. We can visualize the second redescription as a parallel coordinates plot. Using a slider, we can adjust the level of details, i.e. the amount of entities drawn.

.. image:: ../_figs/stories/DBLP/interact/DBLPPick_PacoViewRICDMdetails.gif

5. We can also visualize it under a couple of projections.

.. image:: ../_figs/stories/DBLP/interact/DBLPPick_ViewsSideRICDM.png

6. These various views are linked so that when we select a dot or a subset of dots the will be highlighted across the views.

.. image:: ../_figs/stories/DBLP/interact/DBLPPick_SelectDotSideRICDM.png
	    :class: sideL
.. image:: ../_figs/stories/DBLP/interact/DBLPPick_SelectPolySideRICDM.png
	    :class: sideR

7. We can edit the redescription directly in the parallel coordinate, modifying the bounds of the literal by dragging the bottom and top sides of the gray interval boxes.

.. image:: ../_figs/stories/DBLP/interact/DBLPPick_PacoEditRICDM.png

8. Let's now build another redescription by selecting a pair of conferences and setting their intervals to generate a new left-hand side query.

.. image:: ../_figs/stories/DBLP/interact/DBLPPick_PacoViewExpansionInitRFOCS.png

9. Now we let the algorithm find matching queries for the right-hand side and obtain, for instance, the following redescription.

.. image:: ../_figs/stories/DBLP/interact/DBLPPick_PacoViewExpansionRFOCS.png

.. _uc_finnelec:

Finnish 2011 parliamentary elections (Try it out!)
==================================================

.. note:: 
   In this use case we consider the case of exploring open data about the candidates to a national election using redescription mining :cite:`galbrun_analysing_2016` .
   
   The prepared dataset is available :data_url:`here <vaalikone/>`.

Data
-----

The data was collected from `www.vaalikone.fi <http://www.vaalikone.fi>`_, the *election engine* of the Finnish newspaper Helsingin Sanomat
and `made publicly available <http://blogit.hs.fi/hsnext/hsn-vaalikone-on-nyt-avointa-tietoa>`_. One view contains candidate personal profile attributes, such as party, age, and education, while the answers provided to 30 multiple-choice questions and assigned importance form
the other view.


Exploration
------------

1. Download the :data_url:`data as .siren file <vaalikone/vaalikone.siren>` ( as well as the :data_url:`english translation of the Q&A <vaalikone/vaalikone_translation_eng.txt>`). 

2. Start siren and open the data via :menuselection:`File --> Open`.

3. Explore the premined redescriptions, write and mine new ones, and learn about the finnish political scene...

.. image:: ../_figs/screenshots/Siren_vaalikone_rows.png

4. For instance, duplicate redescription R7 :menuselection:`[Left click on the redescription] --> Duplicate`, open R7 and the copy side-by-side in Parallel Coordinates windows :menuselection:`[Left click on the redescription] --> Parallel Coordinates` and remove the term about the candidate's age from the left-hand side query and see how it affects the accuracy of the redescription...

.. image:: ../_figs/screenshots/Siren_vaalikone.png
