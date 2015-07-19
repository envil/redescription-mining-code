.. _algorithms:

******************************
Mining redescriptions with trees
******************************

There are various strategies for mining redescriptions mining.
We integrated tree-based algorithms to the *Siren* interface to allow mining redescriptions that generalize better, than, for instance redescriptions mine with the greedy *ReReMi* algorithm.
For more details, check the :ref:`references <references>` section.

.. _cartwheels:

CARTWheels (variant available in Siren)
==========================================

The first algorithm introduced for redescription mining was actually based on alternating between constructing CARTs and hence was called the CARTWheels algorithm.

See the little slideshow below to understand how redescriptions are constructed with this approach and read the corresponding publication in the :ref:`references <references>` section for more details.

.. raw:: html

   	<iframe class="inslides" src="../_static/slides_cartwheels.html"></iframe>

.. _cartlayered:

Layered trees
==============

An alternative method for constructing CARTs is to build them layer by layer, we call this method the *layered trees*.


.. raw:: html

   	<iframe class="inslides" src="../_static/slides_layeredtrees.html"></iframe>

.. _cartlayered:

Split trees
============


Finally the third method available in *Siren* construct queries by refining the CART branches separately, we call this method the *split trees*.


.. raw:: html

   	<iframe class="inslides" src="../_static/slides_splittrees.html"></iframe>






