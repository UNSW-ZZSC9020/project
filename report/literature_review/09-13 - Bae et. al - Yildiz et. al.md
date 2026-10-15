# Literature Review Notes: Bae et al. and Yildiz et al.

## Bae, Kwon and Song (2022)

Bae, Kwon and Song (2022) examined how behind-the-meter (BTM) rooftop PV affects observed electricity demand and day-ahead load forecasting. Their key argument is that increasing rooftop PV makes measured grid demand less representative of underlying electricity consumption, because some demand is supplied locally and is therefore not visible to the grid.

To address this, the authors estimated unmetered BTM PV generation and added it back to observed demand to create a reconstructed or *reconstituted load*. An XGBoost model was then trained to forecast this underlying load before estimated PV generation was subtracted again to obtain expected grid demand.

The proposed method outperformed both an LSTM benchmark and an XGBoost model trained directly on observed load, with the improvement strongest during daylight hours. This provides useful evidence that explicitly accounting for rooftop PV can improve demand forecasting rather than relying only on historical demand and weather variables.

This paper is particularly relevant to the project's question of whether including rooftop PV information improves short-term demand prediction. It also provides useful conceptual support for distinguishing underlying electricity consumption from observed grid demand. However, the study used South Korean hourly day-ahead data, so its results are not directly transferable to half-hourly NSW demand modelling. Its BTM PV estimates also relied on assumptions about the relationship between utility-scale and rooftop PV generation.

## Yildiz et al. (2018)

Yildiz et al. (2018) investigated short-term household electricity demand forecasting using smart-meter data from 14 NSW households. The study compared artificial neural networks, support vector regression (SVR), and least-squares SVR across temporal resolutions of 5, 15, 30 and 60 minutes and forecast horizons between 1 and 24 hours.

The authors found that forecasting became more difficult when household demand was highly variable and generally when finer temporal resolutions were used. Aggregating observations into longer intervals smoothed short demand spikes and reduced forecasting error. SVR performed best across most of the tested cases.

The study also grouped days into different load-profile regimes and found that regime-specific forecasting models could improve accuracy. This supports the broader idea that electricity demand relationships can vary under different operating conditions rather than remaining constant over time.

For this project, the paper is mainly useful as methodological background. It highlights the importance of temporal resolution, volatility and changing demand regimes when modelling short-term electricity behaviour. However, it does **not** directly model rooftop PV generation or demonstrate that adding weather variables reduces forecast error during rapid PV changes. The earlier project-plan description should therefore not make those claims.

## Relevance to the Project

Bae et al. (2022) provide direct evidence that explicitly accounting for BTM rooftop PV can improve electricity-demand forecasting, making the paper particularly relevant to the planned comparison between non-PV and PV-enhanced models. Yildiz et al. (2018) provide more general evidence that short-term electricity forecasting is affected by temporal resolution, volatility and changing demand regimes.

Neither paper directly examines how half-hourly changes in rooftop PV affect NSW operational demand under different weather conditions. This leaves a clear role for our project, particularly its planned analysis of PV and demand changes, time-of-day effects, weather interactions and out-of-sample forecasting performance.

## References

Bae, D-J, Kwon, B-S & Song, K-B 2022, 'XGBoost-Based Day-Ahead Load Forecasting Algorithm Considering Behind-the-Meter Solar PV Generation', *Energies*, vol. 15, no. 1, article 128.

Yildiz, B, Bilbao, JI, Dore, J & Sproul, AB 2018, 'Short-term forecasting of individual household electricity loads with investigating impact of data resolution and forecast horizon', *Renewable Energy and Environmental Sustainability*, vol. 3, article 3.