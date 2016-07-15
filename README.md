<p align="center">
<b><a href="#overview">Overview</a></b>
|
<b><a href="#features">Features</a></b>
|
<b><a href="#installation">Installation</a></b>
|
<b><a href="#updating">Updating</a></b>
|
<b><a href="#setup">Setup</a></b>
|
<b><a href="#structure">Structure</a></b>
|
<b><a href="#credits">Credits</a></b>
|
<b><a href="#license">License</a></b>
</p>

![platform](https://img.shields.io/badge/platform-OS%20X%20%7C%20Linux-808080.svg?style=flat-square)
![version](https://img.shields.io/badge/python-v2.7-brightgreen.svg)


# Introduction

One Paragraph of project description goes here

## Getting Started

If you're reading this README from a source distribution, install Beam Profiler
with:

code(python setup.py install)
    
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

Software Features

-------------------------------------------------------
2D Profile                | Beam Peak/Centroid/Ellipse
3D Profile                | Free Rotatable 3D Model
Calculations              | Beam Width (4-Sigma), Beam Diameter, Effective Beam Diameter, Peak Position, Centroid Position, Image Saturation, Total Power, Effective Area, Peak Density, Measured Ellipse Diameter, Ellipticity, Eccentricity, Orientation, Gaussian Ellipse Fit, Diameter
X-Y Profiles              |	Measured Data, Gaussian Fit (Storable)
Plot Positions over Time  | Peak and Centroid Position (Storable)
Power over Time           | Measured Data (Storable)
Pass/Fail Test            | Lockable, Selectable Parameters, Free Choice of Ranges
Beam Stability            | 2D Data of Centroid and Peak Positions over Time
System Requirements       | Windows™ XP SP2, Vista or Later. USB 2.0 Port, 100 MB HD, 512 MB RAM

There are a few limitations:

  * Glass windows: they need to be removed, including the window that is
    typically glued to the chip. Either break it with the chip pointing
    downwards or pull it out while heating the epoxy. This is dangerous
    and will void the camera's warranty. It will also make the chip
    very susceptible to dust and it will age much faster. But it it
    necessary: otherwise fringes will negatively impact image quality.
    Remember that even 1% stray light due to reflections from glass-air
    interfaces leads to 40% peak to peak variations in intensity.

  * ND filters -- reflective or volume absorptive need to be angled
    significantly to keep reflections from interfering at the chip.
    Those filters also need to be of good quality to not distort the
    beam.

  * With front-illuminated silicon chips, wavelengths longer than
    ~1050nm penetrate deeper into the chip and lead to long living
    excitations and smearing of the image along the vertical shift
    direction.

  * Above 1100nm and below 400nm, the quantum efficiency of Silicon
    chips is typically below 5%. Increased powers can destroy the chip
    or bleach it.

  * Monochrome chips are recommended. Otherwise the Bayer color filter
    pattern will skew results.
    
### Features

What can it do?

```
Give examples
```

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
