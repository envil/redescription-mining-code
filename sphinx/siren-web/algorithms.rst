.. _algorithms:

***************
Algorithms
***************

.. note::
   There are various methods for building redescriptions.

   The *ReReMi* algorithm at the core of Siren is a greedy algorithm, but redescriptions can be mined using Classification and Regression Trees (*CART*), too.

Using a greedy update scheme as in *ReReMi*, the original algorithm at the core of *Siren* is one way of mining redescription. An alternative consists of using Classification and Regression Trees (*CART*). Some algorithm from this family can be used through *Siren*.
There are some other approaches too. For more details, check the :ref:`references <references>` section.

.. _algogreedy:

Greedy
=============

.. _algreremi:

ReReMi
------------

The *ReReMi* algorithm is a greedy update scheme for mining redescription that basically tries to find the best atomic extension at each step, constructing queries iteratively. It is presented in the related publications, listed in the :ref:`references <references>` section.

Tree-based
=============

.. _cartlayered:

Layered trees
---------------

An alternative method for constructing CARTs is to build them layer by layer, we call this method the *layered trees*.


.. raw:: html

   	<iframe class="inslides" src="../_static/slides_layeredtrees.html"></iframe>

.. _cartlayered:

Split trees
------------

Finally the third method available in *Siren* construct queries by progressively increasing the depth of the trees, we call this method the *split trees*.


.. raw:: html

   	<iframe class="inslides" src="../_static/slides_splittrees.html"></iframe>

.. _cartwheels:

CARTWheels (a variant is available in Siren)
-------------------------------------

The first algorithm introduced for redescription mining was actually based on alternating between constructing CARTs and hence was called the CARTWheels algorithm.

See the little slideshow below to understand how redescriptions are constructed with this approach and read the corresponding publication in the :ref:`references <references>` section for more details.

.. raw:: html

   	<iframe class="inslides" src="../_static/slides_cartwheels.html"></iframe>


