deployrUtils::deployrPackage("data.table")
deployrUtils::deployrPackage("raster")
deployrUtils::deployrPackage("rasterVis")
deployrUtils::deployrPackage("sqldf")
deployrUtils::deployrPackage("lattice")
deployrUtils::deployrPackage("latticeExtra")

#Parameters
deployrUtils::deployrInput('{"name": "sdp2", "label": "Standard deviation of preference to proximity", "render": "numeric", "default": 0.4, "valueList": [0, 0.1, 0.2, 0.3, 0.4, 0.5]}')
deployrUtils::deployrInput('{"name": "sdb3", "label": "Standard deviation of budget", "render": "integer", "default": 30, "valueRange": [0, 50, 10]}')

sddf = data.frame(sdp = c(0, sdp2, 0), sdbudget = c(0, 0, sdb3))