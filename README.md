# Proyecto 2 BD2

## Introducción 

Para este proyecto, se nos ha pedido crear y un indice invertido utilizando el metodo de SPIMI (Single Pass In-Memory Indexing) en los abstracts de unos articulos web.

### Objetivos
#### Principal
Aplicar los algoritmos de búsqueda y recuperación de la información aprendidos en clase.
#### Secundarios
- Cargar la base de datos sobre la cual se trabajara en el proyecto.
- Trabajar el Score en memoria secundaria 
- Crear una interfaz amigable para la realización de las consultas.


### Organización de Archivos


### Funciones implementadas


### DataSet
El dataset utilizado es arXiv.org, el cual colecciona una vasta cantidad de artículos escolares en las ramas de física, matemáticas, química, computación, entre otras.

![ArXiv](https://upload.wikimedia.org/wikipedia/commons/7/7a/ArXiv_logo_2022.png)
## SQL Parser


### Consultas

### No terminales


## Experimentación

### Front-End

Se utilizó React para la elaboración de la interfaz. Aquí, el usuario colocará la **query** y el **top k** documentos a obtener. Seguidamente, el back-end devolverá el diccionario de los datos y se mostrarán en forma de tabla. Mientras se realiza dicha búsqueda, se mostrara un contador de tiempo de espera de la consulta.

Interfaz al correr la web
![Basico](https://github.com/ByJuanDiego/db2-project-2/assets/68095284/123dd817-07f1-459f-a88f-0b2d2be7e15a)
Interfaz al buscar una query
![Resultado](https://github.com/ByJuanDiego/db2-project-2/assets/68095284/73ef163d-f437-4529-88c7-d15fa47a0b5a)

### Back-End

Se utilizó la macroweb **fastAPI**, con el cual conectamos con el front-end a través de dos endpoints, las cuales son funciones que devolverán el top K de python y de postregs, llamadas **obtener_datos** y **nombre_a_insertar** respectivamente. Para eso, se interpreta la query enviada por el usuario y devuelve la data a través de un JSON.

![image](https://github.com/ByJuanDiego/db2-project-2/assets/68095284/5e8f9356-7039-415b-80ab-ea7edf42183b)

## Conclusiones


## Autores

|                     **Joaquín Jordán**                   |                                 **Juan Diego Castro**                                 |                       **José Chachi**                     |  **Juan Diego Laredo** |
|:---------------------------------------------------------------------------------:|:-------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|:----:|
|           ![Joaquín](https://avatars.githubusercontent.com/u/83974213)            |      ![Juan Diego Castro](https://avatars.githubusercontent.com/u/79115974?v=4)       |              ![José](https://avatars.githubusercontent.com/u/83974741)              | ![Juan Diego Laredo](https://avatars.githubusercontent.com/u/68095284?v=4) |                                             
| <a href="https://github.com/jjordanoc" target="_blank">`github.com/jjordanoc`</a> | <a href="https://github.com/ByJuanDiego" target="_blank">`github.com/ByJuanDiego`</a> | <a href="https://github.com/JoseChachi" target="_blank">`github.com/JoseChachi`</a> | <a href="https://github.com/DarKNeSsJuaN25" target="_blank">`github.com/DarkNeSsJuaN25`</a>|

## Referencias bibliográficas

- [1] C. D. Manning, P. Raghavan, H. Schütze, "Introduction to Information Retrieval". Available: https://nlp.stanford.edu/IR-book/ (accessed Jun. 11, 2023)
