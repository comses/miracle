Analysis Structure: Client Side
===============================

An analysis can have the following special folders

- apps
- data
- docs
- output
- src

`apps`
------

The `apps` folder contains interactive applications for the `Analysis`. These
applications are commonly Shiny or RMarkDown.

`data`
------

The `data` folder contains the all the input data pertaining to the `Analysis`.

`docs`
------

The `docs` folder contains all documentation for the `Analysis`.

`output`
--------

The `output` folder contains all outputs from running a script or application.
This folder is the folder that can contain files that change.

`src`
-----

General code for the `Analysis` goes here. That includes libraries. Application
and source for the `Analysis` must be self contained entities (an application
cannot use code from the `src` folder for now).

Analysis Structure: Server Side
===============================

When an analysis is uploaded, it is broken up into its constituent folders.

Example: The LUXE Analysis
--------------------------

Suppose the LUXE analysis has the following structure:

```
.
└── luxe
    ├── apps
    │   └── luxe
    │       ├── demo_app
    │       │   ├── server.R
    │       │   └── ui.R
    │       └── rmarkdown
    │           └── paper.rmd
    ├── data
    │   └── luxe
    │       └── data.csv
    ├── docs
    │   └── luxe
    │       └── readme.txt
    ├── output
    │   └── luxe
    │       └── output.txt
    └── src
        └── luxe
            ├── script1.R
            └── script2.R

```

Then on the server the analysis broken into its folders matching the structure
below

```
.
└── miracle
    ├── apps
    │   ├── luxe
    │   │   ├── demo_app
    │   │   │   ├── server.R
    │   │   │   └── ui.R
    │   │   └── rmarkdown
    │   │        └── paper.rmd
    │   └── ...
    ├── data
    │   ├── luxe
    │   │   └── data.csv
    │   └── ...
    ├── docs
    │   ├── luxe
    │   │   └── readme.txt
    │   └── ...
    ├── output
    │   ├── luxe
    │   │   └── output.txt
    │   └── ...
    └── src
        ├── luxe
        │   ├── script1.R
        │   └── script2.R
        └── ...
```
