# Additional Literature Review Notes

## Simshauser (2022) — Rooftop solar and demand in the NEM

Simshauser (2022) examined the effect of large-scale rooftop solar uptake on the Queensland region of Australia's National Electricity Market (NEM). The study found that rooftop PV has substantially changed the shape of system demand, particularly by reducing minimum daytime demand. Using a partial-equilibrium model, the paper estimated that around 4,400 MW of installed rooftop PV could displace approximately 1,000 MW of conventional generation capacity. An important finding was that the impact was not limited to reducing peak demand; falling minimum demand also placed pressure on inflexible baseload generation.

This paper is highly relevant because it provides direct Australian NEM evidence that rooftop PV materially changes the shape and operational characteristics of grid demand. While the study focuses on Queensland and longer-term system impacts rather than short-term forecasting, it provides strong context for why changes in rooftop PV should be explicitly considered when modelling NSW operational demand.

**Link:** https://www.sciencedirect.com/science/article/abs/pii/S0140988322001748?via%3Dihub

**Reference:**  
Simshauser, P 2022, 'Rooftop solar PV and the peak load problem in the NEM's Queensland region', *Energy Economics*, vol. 109, article 106002.

---

## Wellby and Engerer (2016) — Weather-driven rooftop PV ramp events

Wellby and Engerer (2016) investigated the meteorological causes of rapid changes in aggregate rooftop PV generation in the Australian Capital Territory. They defined a critical collective ramp as a change equivalent to at least 60% of clear-sky PV potential within one hour and identified 34 such events between January 2012 and July 2014. Positive ramps were commonly associated with events such as the clearing of northwest cloud bands and radiation fog, while major negative ramps were frequently caused by cold fronts and thunderstorms.

This study is particularly relevant to the project's analysis of how the relationship between PV and demand changes under different weather conditions. It provides Australian evidence that large aggregated PV ramps are linked to identifiable meteorological conditions rather than being purely random variation. This supports including cloud cover and other weather variables when analysing changes in rooftop PV output and suggests that extreme PV ramps may need to be considered separately from normal conditions.

**Link:** https://journals.ametsoc.org/view/journals/apme/55/6/jamc-d-15-0107.1.xml

**Reference:**  
Wellby, SJ & Engerer, NA 2016, 'Categorizing the meteorological origins of critical ramp events in collective photovoltaic array output', *Journal of Applied Meteorology and Climatology*, vol. 55, no. 6, pp. 1323–1344.

---

## Stratman et al. (2023) — Disaggregating PV and demand for net-load forecasting

Stratman et al. (2023) proposed a two-stage approach for forecasting electricity net load in areas with high levels of behind-the-meter PV and limited direct observation of individual PV systems. Rather than forecasting net load as a single series, the method first separates observed net load into estimated underlying electricity consumption and PV generation. Separate models are then used to forecast these components before recombining them into a final net-load forecast. The method was tested in two high-PV case studies with fewer than 10% of customers directly observable and produced lower forecasting errors than models that forecast net load directly.

The study is closely related to the project's third research question because it provides further evidence that explicitly representing PV can improve demand forecasting. It also reinforces the conceptual distinction between underlying electricity consumption and the operational demand observed by the grid. Unlike the proposed NSW analysis, however, the paper relies on disaggregation because PV generation is largely unobserved, whereas AEMO provides estimates of aggregate rooftop PV output.

**Link:** https://ieeexplore.ieee.org/document/10125003

**Reference:**  
Stratman, A, Hong, T, Yi, M & Zhao, D 2023, 'Net load forecasting with disaggregated behind-the-meter PV generation', *IEEE Transactions on Industry Applications*, vol. 59, no. 5, pp. 5341–5351.

---

## Shaker, Manfre and Zareipour (2020) — Forecasting aggregated behind-the-meter PV

Shaker, Manfre and Zareipour (2020) developed a method for forecasting the combined output of a large number of distributed behind-the-meter solar systems without requiring measurements from every installation. Their approach used historical generation from a limited number of representative PV systems together with numerical weather prediction data. The method was evaluated against measured generation from 6,673 PV systems in California and achieved an aggregate RMSE of approximately 3%.

This paper is relevant because it demonstrates the importance of weather information when modelling aggregated rooftop PV at a regional scale. Individual rooftop systems can be highly variable, but geographic aggregation produces a smoother regional signal that can still be forecast using representative PV measurements and weather conditions. For the NSW project, this supports combining AEMO's aggregate rooftop PV estimates with weather variables such as cloud cover, solar exposure and temperature. It also provides useful background for interpreting why the PV-demand relationship may change between clear and variable-weather periods.

**Link:** https://www.sciencedirect.com/science/article/abs/pii/S0960148119314405?via%3Dihub

**Reference:**  
Shaker, H, Manfre, D & Zareipour, H 2020, 'Forecasting the aggregated output of a large fleet of small behind-the-meter solar photovoltaic sites', *Renewable Energy*, vol. 147, pp. 1861–1869.

## Parkinson (2025) — Rooftop PV and record-low operational demand in NSW

Parkinson (2025) reports on a record-low electricity-demand event in NSW in February 2025, when rooftop solar supplied around 60% of total demand for the first time in the state. NSW market demand fell to approximately 2,532 MW, around 484 MW below the previous record low. The event occurred despite being in late summer, when minimum-demand records are less common, and coincided with strong solar output, relatively mild temperatures and lower weekend electricity consumption.

The article is particularly relevant to this project because it provides a recent, real-world NSW example of the relationship being investigated. It shows that high rooftop PV output can substantially reduce the operational demand visible to the NEM, while also demonstrating why other factors such as temperature, day of week and underlying consumption need to be controlled for before attributing changes in demand entirely to solar generation. The event also illustrates the value of analysing half-hourly data and periods of unusually high PV output separately, as these conditions can produce demand behaviour that differs substantially from normal periods.

Unlike the peer-reviewed studies in the literature review, this article should be used mainly as contemporary industry context rather than methodological evidence. It provides a useful example of why the research question matters in NSW and could be used in the introduction or motivation section to demonstrate that rooftop PV is already having a measurable effect on operational demand.

*Link:* RenewEconomy, *[“Miles lower:” Rooftop PV takes biggest bite yet out of grid demand in Australia’s biggest coal state](https://reneweconomy.com.au/miles-lower-rooftop-pv-takes-biggest-bite-yet-out-of-grid-demand-in-australias-biggest-coal-state/)*

**Reference:**  
Parkinson, G 2025, '“Miles lower:” Rooftop PV takes biggest bite yet out of grid demand in Australia’s biggest coal state', *RenewEconomy*, 16 February.


