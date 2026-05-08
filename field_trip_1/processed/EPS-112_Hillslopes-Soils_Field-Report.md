# EPS-112 Geomorphology
## Field Report — Caldor Fire Trip
*April 21, 2026*

---

On April 18th, we explored the complex landscape and post-fire mosaic of the Upper Cosumnes watershed on the western flank of the Sierra Nevada east of Pollock Pines, CA. We spent most of our time visiting three soil-mantled hillslopes developing on metasedimentary (Shoo Fly Complex), andesitic (Mehrten Formation), and classic Sierra granodioritic/granitic parent materials, all of which had been variably impacted by the 2021 Caldor Fire.

- At the first (Sly Park, Shoo Fly Complex) and third (Capp's Crossing, Sierra granite) stops, we measured erosion pin heights and dug a soil pit to examine soil formation and horizon development in hillslope soils.
- At the fourth and final stop, we walked the ridgeline across a tor-dotted bedrock landscape and took sporadic soil thickness measurements as we transected back toward the cars.

---

## 1. Direct Measure of Erosion and Sedimentation Along Hillslopes

The erosion pin data we measured at Sly Park and Capp's Crossing is provided separately in two csv files, along with select measurements from the time since the pins were first installed on 10/7/21 (while the Caldor Fire was still raging!). Use these data to inform your answers to the following questions:

**1.1.** Calculate the difference in height between the pins we measured and the pre-storm measurements on 4/9/26. What do you see? What does this suggest for storm-driven sediment transport in this post-fire landscape?

**1.2.** Use the 4/18/26 pin data to assess surface change at the two sites over this past winter (i.e., compare recent measurements against the 10/25/25 data). Describe qualitatively what you see and discuss the implications of this with regards to the seasonality of sediment transport in this post-fire landscape. The figure below can serve as a guide.

![Figure 1: Daily discharge at the Cosumnes River at Michigan Bar (USGS 11335000) and daily precipitation at Sly Park and Pacific House, El Dorado County. Gray arrows mark erosion pin measurement dates. Red shading indicates the Caldor Fire (August–October 2021).](figure1_discharge_precip.png)

*Figure 1: Daily discharge at the Cosumnes River at Michigan Bar (USGS 11335000) and daily precipitation at Sly Park and Pacific House, El Dorado County. Gray arrows mark erosion pin measurement dates. Red shading indicates the Caldor Fire (August–October 2021).*

**1.3.** What is the cumulative change in surface height for each pin from the date of installation through today? (Think about the various ways this could be calculated….) What is the dominant direction of change? Are there variations primarily at intra- and/or inter-hillslope levels? Discuss what this could mean in terms of surface change, sediment (re-)distribution, and landscape recovery over the past ~4.5 years.

**1.4.** When was the biggest change in between sampling intervals? When was the biggest change when normalized for time (between measurements)? Does this make sense with seasonal or yearly precipitation trends in the study area?

**1.5.** Based on the BAER soil burn severity index, soil burn severity was low to moderate at the Sly Park site and moderate to severe at Capp's Crossing. Discuss the erosion pin time series from each site in the context of this burn severity differential. What else is different about the two sites that could help reconcile what might initially appear to be surprising erosion pin data?

**1.6.** Think about the patterns in erosion pin heights at the intra- (within) hillslope level. Assuming this ~5-year record is representative, what does this suggest about the evolution of the two hillslopes in the modern day?

---

## 2. Soil Thickness and Threshold Landscapes

**2.1.** Think back to our final stop at the main core site at the hillslope underlain by andesitic tuffs and ignimbrites of the Mehrten Formation. Now think back to George's lecture on hillslope processes and Gilbert's law of divides and law of structure. Which (or both) of these laws seemingly applies at the scale of the hillslope soil thickness transect at stop 4? Which (or both) seemingly applies at the landscape scale across the broader field area?

**2.2.** Hilltop curvature ($C_{HT}$) is $-0.0077\ \text{m}^{-1}$ on canyon-adjacent ridges near stop 1 (Sly Park erosion pins), $-0.0030\ \text{m}^{-1}$ on the interfluves surrounding Capp's Crossing at stop 3, and $-0.0027\ \text{m}^{-1}$ on the andesitic ridges like the one we walked up to at stop 4. Calculate the diffusivity/soil transport coefficient $K$ ($\text{L}^2/\text{T}$) assuming a long-term erosion rate of $24\ \text{m Myr}^{-1}$ for hillslopes in Mehrten andesites, $33\ \text{m Myr}^{-1}$ for the granites, and $49\ \text{m Myr}^{-1}$ for the Shoo Fly metasedimentary hillslopes adjacent to the canyon.

**2.3.** Use the quantities you derived (as well as those that were given) in 2.2 to validate your answer to 2.1. In other words, describe how $C_{HT}$, $E$, and $K$ inform hillslope form and the competition between the law of divides vs the law of structure across the study area.

---

## 3. Sediment Transport on Hillslopes Across Timescales

The Sly Park and Capps Crossing landscape attribute tables supply values for slope and the Laplacian (analogous to curvature in hillslope form/diffusion equations) along the erosion pin transects. The soil thickness table supplies these same quantities for the andesitic hillslope at stop 4 where we measured our soil thickness transects.

**3.1.** Using the associated landscape attribute tables and your erosion pin data from Sly Park and Capp's Crossing, calculate: A) the long-term sediment flux per unit contour length (in $\text{kg m}^{-2}\ \text{yr}^{-1}$) expected at each pin, and B) the short-term sediment flux per unit contour length (in $\text{kg m}^{-2}\ \text{yr}^{-1}$) from your derived pin length changes assuming the typical bulk density value of $1.3\ \text{g cm}^{-3}$ from the geomorphic literature. How do these quantities compare? What does this suggest in terms of sediment transport behavior over the past ~4.5 years in this post-fire landscape relative to the long-term averages?

**3.2.** Now re-calculate your short-term sediment flux estimates using measured BD values of $0.57\ \text{g cm}^{-3}$ at Sly Park and $1.35\ \text{g cm}^{-3}$ at Capp's Crossing. Does this change your previous conclusions? What happens to your soil transport coefficients if you pin them to the short vs. long-term values?

**3.3.** Calculate the range of residence times for soils on these slopes. How many pulses of elevated erosion would be needed to account for the total amount of long-term surface lowering under the max and min residence time scenarios?

**3.4.** Now calculate the range of residence times for soils on the andesitic ridgelines. Discuss the factors that might be driving the differences in mean particle residence times across all 3 sites.

**3.5.** Create a plot of soil thickness as a function of the Laplacian curvature. What does this relationship suggest? Based on this relationship and what we saw out in the field, does the soil production framework seem like it matches what we can observe on the landscape? If so, which form of the soil production function would seemingly be most applicable to this site? If not, discuss how the spatial variations in soil thickness observed here are at odds with the SPF.
