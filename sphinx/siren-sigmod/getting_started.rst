.. _started:

*****************
Getting Started
*****************

.. note::
   *Siren* allows you to interactively mine and visualize redescriptions from your data.

   We outline here some high-level interactions offered by *Siren*.

.. _importing_data:

Importing data
==================

After you get *Siren* installed and running, it will open the :ref:`tools window <tools_window>`, with tabs for variables and redescriptions, all of them empty. Hence, the first thing to do is to import data or open an existing siren package to start working.    

If you already have some siren package (i.e. with a ``.siren`` extension) you can open it via the interface menu :menuselection:`File --> Open`.


Otherwise, or if you want to work on a new data set, you can :ref:`import data <data_formats>` to *Siren*, this will populate the ``Entities`` and ``Variables`` tabs.

.. _mining_scratch:

Mining redescriptions from scratch
===================================

Once the two sets of variables are loaded and can be seen in the tabs you may want to let the tool mine redescriptions in an fully automated way, using currently enabled variables. The menu entry :menuselection:`Process --> Mine` redescriptions let you do just that.

Alternatively, if both queries in a visualization are empty *Siren* simply mines redescriptions on your data when clicking on the ``Expand`` button.

Results will be appended to the redescriptions list in the ``Expansions`` tab.

Before running a mining task make sure you have adjusted the `mining preferences <_static/miner_confdef.xml>`_...

.. _expanding_red:

Expanding a redescription
==========================

You can also press the expansion button to automatically find expansions of any redescription your are currently visualizing and editing.
*Siren* will try to append literals to the current redescription, using the enabled variables. 

Again, results will be appended to the redescriptions list in the ``Expansions`` tab.

Before running an expansion task make sure you have adjusted the `mining preferences <_static/miner_confdef.xml>`_...


.. _filtering_red:

Filtering redescriptions
=========================

A list of redescription can be filtered automatically. That is, the algorithm will go through the redescriptions, from top to bottom in the current order, an check for each redescription, whether it is redundant given the previous ones. If a redescription is found redundant it will be disabled. This is done via the interface menu :menuselection:`Edit --> Filter redundant`.

It is also possible to select a redescription and filter following redescriptions which are redundant to that particular redescription only, via the interface menu :menuselection:`Edit --> Filter redundant` to current.


.. _exporting_reds:

Exporting redescriptions
==========================

The redescriptions from the *Redescriptions* tab can be exported under :ref:`different formats <export>`.


.. _saving_package:

Saving as a package
====================

You can save your current project, i.e. the data, current redescription list and preferences as a siren package (i.e. with a ``.siren`` extension) via the interface menu :menuselection:`Edit --> Save as`...

If you continue working on the current project you can save changes to the current siren package via the interface menu :menuselection:`Edit --> Save`.

Existing siren packages can be opened via the interface menu :menuselection:`File --> Open`.
