# Proyecto 2 BD2

## Introducción 

Para este proyecto, se nos ha pedido crear y un indice invertido utilizando el metodo de SPIMI (Single Pass In-Memory Indexing) en los abstracts de unos articulos web.

## Objetivos
### Principal
Aplicar los algoritmos de búsqueda y recuperación de la información aprendidos en clase en memoria secundaria.
### Secundarios
- Cargar la base de datos sobre la cual se trabajara en el proyecto.
- Crear una interfaz amigable para la realización de las consultas.


## Descripción del dominio de datos
El dataset utilizado es un extracto arXiv.org, el cual colecciona una vasta cantidad de artículos escolares en las ramas de física, matemáticas, química, computación, entre otras.

![ArXiv](https://upload.wikimedia.org/wikipedia/commons/7/7a/ArXiv_logo_2022.png)

El formato del documento es una lista de objetos JSON con la siguiente información:

```json
"id": "0704.0001"
"submitter": "Pavel Nadolsky"
"authors": "C. Balazs, E. L. Berger, P. M. Nadolsky, C.-P. Yuan"
"title": "Calculation of prompt diphoton production cross sections at Tevatron and LHC energies"
"comments": "37 pages, 15 figures; published version"
"journal-ref": "Phys.Rev.D76:013009,2007"
"doi": "10.1103/PhysRevD.76.013009"
"report-no": "ANL-HEP-PR-07-12"
"categories": "hep-ph"
"license": ""
"abstract": " A fully differential calculation in perturbative quantum chromodynamics is presented for the production of massive photon pairs at hadron colliders. All next-to-leading order perturbative contributions from quark-antiquark, gluon-(anti)quark, and gluon-gluon subprocesses are included, as well as all-orders resummation of initial-state gluon radiation valid at next-to-next-to-leading logarithmic accuracy. The region of phase space is specified in which the calculation is most reliable. Good agreement is demonstrated with data from the Fermilab Tevatron, and predictions are made for more detailed tests with CDF and DO data. Predictions are shown for distributions of diphoton pairs produced at the energy of the Large Hadron Collider (LHC). Distributions of the diphoton pairs from the decay of a Higgs boson are contrasted with those produced from QCD processes at the LHC, showing that enhanced sensitivity to the signal can be obtained with judicious selection of events. "
"versions": []
"update_date": "2008-11-26"
"authors_parsed": []
```

Dataset extraído de [Kaggle](https://www.kaggle.com/datasets/Cornell-University/arxiv).

## Back-End

Se utilizó el framework **FastAPI**, con el cual conectamos con el front-end a través de dos endpoints, los cuales devolverán el top K de nuestro indice creado y PostgreSQL. Para eso, se interpreta la query enviada por el usuario y se devuelve la data a través de un JSON.

### Contrucción del índice invertido

En la construcción del índice invertido en memoria secundaria se utilizó el algoritmo **Single Pass In-Memory Indexing (SPIMI)**. 
Se adaptó este algoritmo, que sirve para crear índices invertidos para el modelo de recuperación booleana, para realizar consultas por ranking.
Para hacer esto, al momento de computar las listas de postings de cada término se agregó la frecuencia de término, que posteriormente nos ayudará a computar los pesos tf-idf para la búsqueda por texto. 

Para implementar este algoritmo, se tomó como referencia la siguiente implementación de la función SPIMI-Invert: ![Referencia](https://slideplayer.com/slide/7351989/24/images/4/Merging+of+blocks+is+analogous+to+BSBI.jpg)

Una vez se construyeron los índices invertidos locales usando SPIMI-Invert, se combinaron usando la estrategia de k-way merge en memoría secundaria.
Se implementó usando un heap de tamaño k que guarda el mínimo término siendo procesado en cada documento.

#### Diagrama del proceso

![image](https://github.com/ByJuanDiego/db2-project-2/assets/83974213/27b26126-7061-4b61-a36c-8b726f25a534)

### Manejo de memoria secundaria

Se utilizó la memoria secundaria para guardar los resultados de los índices invertidos parciales en el SPIMI-Invert, y también en el merge.
También se utilizó la memoria secundaria para persistir cierta información relevante como la cantidad de términos en el índice invertido y la cantidad de documentos total (que nos sirve posteriormente para calcular el tf-idf). 

### Ejecución óptimo de consultas

Para realizar una consulta óptima se ha considerado tanto la complejidad espacial como la complejidad computacional. Se tomó como guía el siguiente pseudocódigo:

![Cosine_Score](https://github.com/ByJuanDiego/db2-project-2/assets/83974741/25d0d216-1b66-4417-a102-fde2342fa369)

Para la implementación de las consultas, se consideró ya un cálculo de las normas de cada documento. Es inevitable manejar un arreglo en donde se guarden los documentos con sus respectivos scores, debido hay que considerar todos los documentos para posteriormente ordenarlos.
En el caso de los cálculos del score por documento, solo se está iterando por cada término de la query en la colección total de términos de todos los documentos existentes. Básicamente se está aplicando una intersección debido a que estamos accediendo a memoria secundaria. Además de ello, cabe señalar que se está realizando una búsqueda binaria de un término en la colección total de términos. Esto es para optimizar de manera notable las lecturas en memoria secundaria.


## Frontend

Se utilizó React para la elaboración de la interfaz. Aquí, el usuario colocará la query y el top k documentos a obtener. Al presionar el botón de **enviar**, se realizará una conexión con las funciones del back-end (una para nuestro índice invertido y otra para Postgres), enviando como parámetros dichas variables. Seguidamente, la página esperará hasta que cada función devuelva un diccionario de los datos obtenidos, para después mostrarlos en formato de tabla, con el tiempo de consulta de cada uno.

Interfaz al correr la web
![Basico](https://github.com/ByJuanDiego/db2-project-2/assets/68095284/123dd817-07f1-459f-a88f-0b2d2be7e15a)
Interfaz al buscar una query
![Resultado](https://github.com/ByJuanDiego/db2-project-2/assets/68095284/73ef163d-f437-4529-88c7-d15fa47a0b5a)



## Conclusiones


## Autores

|                     **Joaquín Jordán**                   |                                 **Juan Diego Castro**                                 |                       **José Chachi**                     |  **Juan Diego Laredo** |
|:---------------------------------------------------------------------------------:|:-------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|:----:|
|           ![Joaquín](https://avatars.githubusercontent.com/u/83974213)            |      ![Juan Diego Castro](https://avatars.githubusercontent.com/u/79115974?v=4)       |              ![José](https://avatars.githubusercontent.com/u/83974741)              | ![Juan Diego Laredo](https://avatars.githubusercontent.com/u/68095284?v=4) |                                             
| <a href="https://github.com/jjordanoc" target="_blank">`github.com/jjordanoc`</a> | <a href="https://github.com/ByJuanDiego" target="_blank">`github.com/ByJuanDiego`</a> | <a href="https://github.com/JoseChachi" target="_blank">`github.com/JoseChachi`</a> | <a href="https://github.com/DarKNeSsJuaN25" target="_blank">`github.com/DarkNeSsJuaN25`</a>|

## Referencias bibliográficas

- [1] C. D. Manning, P. Raghavan, H. Schütze, "Introduction to Information Retrieval". Available: https://nlp.stanford.edu/IR-book/ (accessed Jun. 11, 2023)
