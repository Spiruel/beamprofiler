# Beam Profiler

One Paragraph of project description goes here

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

Software Features

2D Profile | Beam Peak/Centroid/Ellipse
3D Profile | Free Rotatable 3D Model
Calculations | Beam Width (4-Sigma), Beam Diameter, Effective Beam Diameter, Peak Position, Centroid Position, Image Saturation, Total Power, Effective Area, Peak Density, Measured Ellipse Diameter, Ellipticity, Eccentricity, Orientation, Gaussian Ellipse Fit, Diameter
X-Y Profiles |	Measured Data, Gaussian Fit (Storable)
Plot Positions over Time | Peak and Centroid Position (Storable)
Power over Time | Measured Data (Storable)
Pass/Fail Test | Lockable, Selectable Parameters, Free Choice of Ranges
Beam Stability | 2D Data of Centroid and Peak Positions over Time
System Requirements | Windows™ XP SP2, Vista or Later. USB 2.0 Port, 100 MB HD, 512 MB RAM

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
    
### Prerequisities

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you have to get a development env running

Stay what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* Dropwizard - Bla bla bla
* Maven - Maybe
* Atom - ergaerga

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
