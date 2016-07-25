# Beam Profiler

Beam Profiler is a laser beam analysis application written in Python and intended for use with cheap webcams.

Beam Profiler interfaces with a webcam using OpenCV (Open Source Computer Vision Library) and uses Tkinter, Python's de-facto standard GUI (Graphical User Interface) package.
In the interests of making the code easy to use, libraries that are typical to most standard Python distributions were favoured. This includes the powerful scientific libraries such as Numpy and Scipy, as well as the plotting library Matplotlib.

The purpose of this project is to produce an application that is both open-source, cross-platform, and designed for inexpensive hardware.
Professional laser beam profilers tend to be expensive, using patented algorithms with concealed methods.
When researchers release public data that use these methods, there is no way of knowing what was specifically measured.
Because of this, it is important that this analysis software is made freely available and open-source for publicly-funded research.

## Getting Started

###Installation

Beam Profiler may be installed using Pip. Simply install using, 

```
pip install BeamProfiler
```

If you're reading this README from a source distribution, install Beam Profiler
with:

```
python setup.py install
```
    
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

Download sources for Windows™ or Macintosh™ platforms are available here:

Once successfully installed, simply run ```get_profile.py``` with a connected webcam to get started.

###Modifying the webcam

Beam Profiler is compatible with any camera that works with the OpenCV library. This means almost all webcams and several other high-quality CCDs.

There are a considerations that should be taken into account before using the application:

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

  * Above 1100 nm and below 400 nm, the quantum efficiency of Silicon
    chips is typically below 5%. Increased powers can destroy the chip
    or bleach it.

  * Monochrome chips are recommended. Otherwise the Bayer colour filter
    pattern will skew results.

## Features

* Calculations              
 Beam Width (4-Sigma), Beam Diameter, Peak Pixel value, Peak Position, Centroid Position, Power Density, Measured Ellipse Axes, Ellipticity, Eccentricity, Orientation|
* 2D Profile                
 Beam Peak/Centroid/Ellipse
* 3D Profile                
 Free Rotatable 3D Model
* X-Y Profiles              
 Measured Data, Gaussian Fit (Storable)
* Plot Positions over Time  
 Peak and Centroid Position (Storable)
* Power over Time           
 Measured Data (Storable)
* Pass/Fail Test            
 Selectable Parameters with alerts avaialble when values fall out of the specified range
* Beam Stability            
 2D Data of Centroid and Peak Positions over Time
* Background frame calibration
* Save Screenshots and Videos to disk
* Switch between multiple cameras as the application is running
* Rotate the input frame instead of rotating the laser
* Save settings to a simple config file, allowing specific configurations depending on the choice of webcam and laser

## How to use
Upon loading the application, you will be presented with a camera feed and a default workspace. This can be configured as desired.
The space hotkey will toggle the profiler's state, where upon activated it will immediately begin calculations on what the computer receives from the webcam.
Changes to exposure time, region of interests and so on may require further configuration before you can use the profiler effectively. These can be adjusted in the control menu. 

All the results and plots are directly accessed using the window menu. All of this available data can be exported at any time to a .csv in the file menu.

## Authors

* **Samuel Bancroft** - *Summer Student at Birmingham University*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc