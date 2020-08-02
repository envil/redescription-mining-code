.. _algorithms:

***************
Algorithms
***************

.. note::
   There are various methods for building redescriptions.

   *Siren* allows to mine redescription using the greedy *ReReMi* algorithm as well as the *splittrees* and *layeredtrees* algorithms based on Classification and Regression Trees (*CART*).

   For more details, check the original publications in the :ref:`references <references>` section.

.. _algogreedy:

Greedy
=============

.. _algreremi:

ReReMi
------------

The *ReReMi* algorithm :cite:`galbrun_black_2012` is a greedy update scheme for mining redescription that basically tries to find the best atomic extension at each step, constructing queries iteratively.

Tree-based
=============

.. _cartwheels:

CARTWheels (a variant is available in *Siren*)
--------------------------------------------------

The first algorithm introduced for redescription mining was actually based on alternating between constructing CARTs and hence was called the CARTWheels algorithm :cite:`ramakrishnan_turning_2004`.

See the little slideshow below to understand how redescriptions are constructed with this approach and refer to the original publication for more details.

.. raw:: html

   	<iframe class="inslides" src="../_static/slides_cartwheels.html"></iframe>


Layeredtrees
---------------


An alternative method for constructing CARTs is to build them layer by layer. This method is implemented by the *layeredtrees* algorithm :cite:`zinchenko_mining_2015`.


.. raw:: html

   	<iframe class="inslides" src="../_static/slides_layeredtrees.html"></iframe>

.. _cartlayered:

Splittrees
------------

Finally the third method available in *Siren* construct queries by progressively increasing the depth of the trees. This method is implemented by the *splittrees* algorithm :cite:`zinchenko_mining_2015`.


.. raw:: html

   	<iframe class="inslides" src="../_static/slides_splittrees.html"></iframe>



