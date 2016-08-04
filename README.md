# BiLBO (Birmingham Laser Beam Observer)
![Main toolbar information](https://cloud.githubusercontent.com/assets/3259632/17398154/426428a2-5a33-11e6-897e-15d9760fd5c2.png)

BiLBO is a laser beam analysis application written in Python and intended for use with cheap webcams.

BiLBO interfaces with a webcam using OpenCV (Open Source Computer Vision Library) and uses Tkinter, 
Python's de-facto standard GUI (Graphical User Interface) package.
In the interests of making the code easy to install and make use of, libraries that are typical to most standard Python distributions 
were favoured for use. This includes the powerful Numpy and Scipy scientific libraries, as well as the plotting library Matplotlib. 
If you do not yet have a Python distribution installed, it is reccommended that you use the [Anaconda distribution](https://www.continuum.io/downloads).

The purpose of this project is to produce an application that is both open-source, cross-platform, and designed for inexpensive hardware.
Professional laser beam profilers tend to be expensive, using patented algorithms with concealed methods.
When researchers release public data that use these methods, there is no way of knowing what was specifically measured.
Because of this, it is important that this analysis software is made freely available and open-source for publicly-funded research.

## Getting Started

###Installation

####Quick Start
These instructions will get you a copy of the project up and running on your local machine.

First, you can to try to run this command in your terminal,

```
python -c "import urllib2;exec(urllib2.urlopen('https://raw.githubusercontent.com/Spiruel/beamprofiler/master/installation.py').read())" 
```

to install everything (except OpenCV) at once and download necessary files into your working directory.

####Install from source distribution
Alternatively you can download a copy of this repository, and run:

```
pip install -r requirements.txt
```

in order to install the required dependencies (except OpenCV) for BiLBO to work. 

####OpenCV Installation
You will now need to install the OpenCV library separately. [Source download here](http://sourceforge.net/projects/opencvlibrary/files/opencv-win/). 
[Alternatively, Unofficial Windows Binaries for pip installation of OpenCV .whl file here.](http://www.lfd.uci.edu/~gohlke/pythonlibs/).

**Note**: If you're on the Anaconda distribution of Python you can try to easily install OpenCV using,

```
conda install opencv
```
####Executables
Download for Windows™ platforms available here:

###Modifying the webcam

BiLBO is compatible with any camera that works with the OpenCV library. This means almost all webcams and several other high-quality CCDs.

There are a considerations that should be taken into account before using the application:

  * Glass windows will need to be completely removed, including the glass cover that is
    typically glued to the front of the CCD chip. You can remove this by applying heat 
    to the epoxy with a heat gun. It is to important to remember that removing with cover this will make the chip
    very vulnerable to dust and it will age much faster. But it it
    absolutely necessary to prevent interferences fringes negatively impacting upon the quality of the image.
    Even 1% stray light due to reflections from glass-air
    interfaces leads to 40% peak to peak variations in intensity.

  * With front-illuminated silicon CCD chips, wavelengths longer than
    around 1050 nm penetrate deeper into the chip and lead to long lasting
    excitations and image smearing along the vertical shift
    direction.

  * Above 1100 nm and below 400 nm, the quantum efficiency of silicon
    chips is expected to be below 5%. Increased powers incident on the CCD can destroy the chip
    or bleach it.

  * Monochrome chips are recommended - the Bayer colour filter
    pattern will skew results.
    
###How to begin
(Click to enlarge image.)
![](https://cloud.githubusercontent.com/assets/3259632/17398152/3f943c52-5a33-11e6-95d6-2247db34b619.png)

When the programme loads, the main control bar will load alongside any configured workspace arrangement. It is reccommended that you familiarise yourself
with the controls before activating the profiler. The main control bar contains almost all the controls, with the other windows predominately for display
purposes.

####Main navigation bar
Using the five navigation menus located at the top of the control bar, you can export data, calibrate background subtraction, change the camera view and more.
For a full list of features please look at [features](#features).

####Main toolbar
(Click to enlarge image.)
![Main toolbar information](https://cloud.githubusercontent.com/assets/3259632/17363802/8b730d5c-5974-11e6-861a-0fceac70c36d.png)

## How to use

Please follow these steps in order to make full use of BiLBO:

1. Load the application by running ```python get_profile.py```.
2. While the profiler is deactivated, configure your workspace as desired, adjusting the exposure etc if it's not been pre-defined in the config file beforehand.
3. Open the webcam view and align your laser so that the beam shape is fully enclosed in the webcam view.
4. Turn off the laser and perform a background subtraction calibration. Monitor the pixel value data in both the calculation results window and webcam view to ascertain its success.
5. Activate the profiler with the space hotkey or the checkbox, and you're good to go!

Upon loading the application, you will be presented with a camera feed, and if a valid configuration file exists, a workspace arrangement as well. This can be configured as desired.
The space hotkey will toggle the profiler's state, where upon activated it will immediately begin calculations on what the computer receives from the webcam.
Changes to exposure time, regions of interest and so on may require further configuration before you can use the profiler effectively. These can be adjusted in the control menu. 

All the results and plots are directly accessed using the window menu. All of this available data can be exported at any time to a .csv in the file menu.

## Features
![](https://cloud.githubusercontent.com/assets/3259632/17398149/3d49a3ba-5a33-11e6-9210-9cd9a8360231.png)

* **Calculations**            
 Beam Width (1/e^2), Beam Diameter, Peak Pixel value, Peak Position, Centroid Position, Power Density, Measured Ellipse Axes, Ellipticity, Eccentricity, Orientation
 (Exportable)
* **2D Profile**               
 Beam Peak/Centroid/Ellipse overlays
* **3D Profile**              
 Free Rotatable 3D Model using MayaVi
* **X-Y Cross Profiles**          
 Measured Data, Gaussian Fit
* **Plot Positions over Time**           
 Peak and Centroid x and y positions (Exportable)
* **Pass/Fail Testing**        
 Selectable Parameters with alerts available when values fall out of the specified range
* **Beam Stability**           
 2D data of Centroid and Peak Positions over Time
* **And**
  * Background frame calibration
  * Save Screenshots and Videos to disk
  * Switch between multiple cameras as the application is running
  * Rotate the input frame instead of rotating the laser
  * Save settings to a simple config file, allowing specific configurations depending on the choice of webcam and laser
  * Active ellipse drawing on webcam real-time view, with a large cross marking any active centroid and the smaller cross marking any active peak of the identified laser beam.
  * Fully configurable, with custom toolbar configuration and window layout workspaces all available to be saved to a file and loaded on request

##FAQ

###When I activate the profiler the programme is slow to respond, with a low refresh rate. What steps should I take to fix this?
BiLBO is designed to work on a range of computer, but some will perform better than others. If you find that your computer is not powerful enough to run
the application well, try these steps:
  1. Reduce the resolution of the webcam view in the config.ini file. Note: You will need to adjust the pixel scale parameter in accordance with this.
Measurement accuracy will be affected by this.  
  2. Configure your workspace to reduce the number of active plots. Don't worry: Crucial data is still collected behind the scenes and can be exported at any point.
  3. Reduce the plot refresh rate in the config to reduce the rate of canvasses being actively refreshed.
  4. Close the webcam view window if it is active.

###I want to add new features to BiLBO and offer improvements.
Feel free to offer pull requests etc to this repository!

###I have an issue which I am struggling to diagnose. It is probably a bug.
Please create an issue in the repository issues page and it will get investigated!

## Authors

* **Samuel Bancroft** - *Summer Student at Birmingham University*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thank you to my supervisor Dr Jon Goldwin.
* Thanks to the [Ogden Trust](www.ogdentrust.com) for allowing this internship to be possible.
* Thanks to Ben Bancroft for helping me with code problems...