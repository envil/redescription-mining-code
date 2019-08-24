.. _started:

*****************
 Getting Started
*****************

.. note::
   *Siren* allows you to interactively mine and visualize redescriptions from your data.

   We outline here some high-level interactions offered by *Siren*.


Because examples are worth many words, :data_link:`here <toys/>` are some datasets to try your hands on. 

.. _importing_data:

1. Load data
==================

After you get *Siren* installed and running, it will open the :ref:`tools window <tools_window>`, with tabs for variables and redescriptions, all of them empty. Hence, the first thing to do is to import data or open an existing siren package to start working.    

If you already have some siren package (i.e. with a ``.siren`` extension) you can open it via the interface menu :menuselection:`File --> Open`.


Otherwise, or if you want to work on a new data set, you can :ref:`import data <data_formats>` to *Siren*, this will populate the ``Entities`` and ``Variables`` tabs.

.. _mining_scratch:

2. Mine redescriptions
===================================

Once the two sets of variables are loaded and can be seen in the tabs you may want to let the tool mine redescriptions in an fully automated way, using currently enabled variables. The menu entry :menuselection:`Process --> Mine` redescriptions let you do just that.

Alternatively, if both queries in a visualization are empty *Siren* simply mines redescriptions on your data when clicking on the ``Expand`` button.

Results of the mining process will appear in a new list in the ``Redescriptions`` tab.

Before running a mining task make sure you have adjusted the main :ref:`mining parameters <mining_parameters>`...

.. _viz_edit_red:

3. Visualize and edit redescriptions
========================================

.. _visualizing_red:

Visualizing a redescription
-----------------------------

Individual redescriptions and lists can be plotted in different visualizations, depending on the type of your data and the redescriptions.

Double-click on an item (variable, redescription, list) to open the default visualization for that item. The :menuselection:`View` entry in the main menu and under the contextual menu list available visualizations.


.. _expanding_red:

Expanding a redescription
--------------------------

You can also press the expansion button to automatically find expansions of any redescription your are currently visualizing and editing.
*Siren* will try to append literals to the current redescription, using the enabled variables. 

Again, results will be appended to the redescriptions list in the ``Expansions`` tab.

Before running an expansion task make sure you have adjusted the :ref:`mining parameters <mining_parameters>`...


.. _filtering_red:

Filtering redescriptions
--------------------------

A list of redescription can be filtered automatically. That is, the algorithm will go through the redescriptions, from top to bottom in the current order, an check for each redescription, whether it is redundant given the previous ones. If a redescription is found redundant it will be disabled. This is done via the different filter entries in the :menuselection:`Edit` menu .

.. _exporting_reds:

Exporting redescriptions
--------------------------

The lists of redescriptions from the *Redescriptions* tab can be exported under :ref:`different formats <export>` from the contextual menu.


.. _saving_package:

Saving as a package
--------------------------

You can save your current project, i.e. the data, current redescription lists and parameter preferences as a siren package (i.e. with a ``.siren`` extension) via the interface menu :menuselection:`Edit --> Save as`...

If you continue working on the current project you can save changes to the current siren package via the interface menu :menuselection:`Edit --> Save`.

Existing siren packages can be opened via the interface menu :menuselection:`File --> Open`.

Lists of redescriptions can be added and deleted from a package. A package needs to be first created before redescriptions lists can be added to it.


.. _iterate:

Iterate...
========================================

The data analysis process typically require a few iterations of mining, looking at the results, tuning the parameters, etc.
