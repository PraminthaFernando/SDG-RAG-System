import logging

def setup_logger(name="carbon_rag"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

SDG_PROTOTYPES = {
    "SDG_1": {
        "1.1.1": [
            "Baseline socio-economic surveys indicated that households were living below the international poverty line (USD 2.15/day).",
            "Disaggregated analysis shows female-headed households were below the international poverty threshold.",
            "Project-supported livelihood activities reduced the proportion of extremely poor households.",
            "Unemployed youth were below the international poverty line at baseline.",
            "Forest-dependent communities exhibited higher poverty incidence."
        ],

        "1.2.1": [
            "Households were below the national poverty line at baseline.",
            "Female-headed households showed higher poverty incidence.",
            "Reduction in households living below the national poverty line.",
            "Youth-headed households below national poverty threshold.",
            "Income diversification reduced vulnerability among poor households."
        ],

        "1.2.2": [
            "Households experienced multidimensional poverty including lack of water and electricity.",
            "Interventions improved multidimensional poverty indicators.",
            "Education and health programs improved well-being indicators.",
            "Women beneficiaries improved empowerment and income stability.",
            "Multidimensional poverty declined across income, health and education."
        ],

        "1.3.1": [
            "Payment for Ecosystem Services provide income transfers.",
            "Carbon revenue distributed through benefit-sharing agreements.",
            "Vulnerable households receive priority access to PES payments.",
            "Formalized income support mechanisms linked to conservation.",
            "Verification determines eligibility for continued PES participation."
        ],

        "1.4.1": [
            "Water infrastructure increased access to drinking water.",
            "Solar systems improved electricity access in villages.",
            "Sanitation facilities constructed in community schools.",
            "Access to health facilities increased.",
            "Basic service access improvements prioritized for underserved communities."
        ],

        "1.4.2": [
            "Project covers land owned by Indigenous Community Ownership Groups.",
            "Landholders possess legally recognized tenure documentation.",
            "Community perception of land tenure security increased.",
            "Land titles verified and legally enforceable.",
            "Secure tenure arrangements support long-term conservation."
        ]
    },

    "SDG_2": {
        "2.1.2": [
            "Households experienced moderate food insecurity.",
            "Severe food insecurity declined during monitoring.",
            "Agroforestry improved seasonal food availability.",
            "Food insecurity higher among landless households.",
            "Dietary diversity scores improved."
        ],

        "2.3.1": [
            "Agroforestry productivity increased per labour unit.",
            "Cocoa yields improved per hectare.",
            "Labour productivity increased following training.",
            "Pasture productivity improved.",
            "Forest enterprises increased value added per worker."
        ],

        "2.3.2": [
            "Income of smallholders increased.",
            "Female small-scale producers reported income growth.",
            "Indigenous landholders received PES payments.",
            "Agroforestry increased household income.",
            "Sustainable land management diversified income."
        ],

        "2.4.1": [
            "Land transitioned to sustainable agroforestry systems.",
            "Farms adopted soil conservation practices.",
            "Deforestation-free production implemented.",
            "Sustainable pasture management reduced pressure on forests.",
            "Land-use planning aligned with REDD+ safeguards."
        ]
    },

    "SDG_3": {
        "3.8.1": [
            "Patients received diagnostic services.",
            "Rural clinics renovated to improve service delivery.",
            "Health access improved for remote communities.",
            "Medical outreach expanded using carbon revenue.",
            "Essential health services coverage increased."
        ],

        "3.9.1": [
            "Avoided deforestation reduced biomass burning emissions.",
            "Reduction in forest fires improved air quality.",
            "Charcoal reliance decreased.",
            "Emission reductions lowered ambient pollution exposure.",
            "Forest cover improved air quality regulation."
        ]
    },

    "SDG_4": {
        "4.3.1": [
            "Students received bursary support.",
            "Agricultural training sessions conducted.",
            "Participants attended capacity-building workshops.",
            "Girls represented significant bursary recipients.",
            "Youth participation in training increased."
        ],

        "4.4.1": [
            "Landholders received restoration training.",
            "Rangers completed MRV certification.",
            "Community trained in carbon monitoring.",
            "Entrepreneurship training supported MSMEs.",
            "Technical skills improved in agroforestry."
        ]
    },

    "SDG_5": {
        "5.5.2": [
            "Managerial positions held by women.",
            "Female landholders represented among beneficiaries.",
            "Female employees engaged in project operations.",
            "Women representation increased in governance.",
            "Gender parity targets monitored annually."
        ]
    },

    "SDG_6": {
        "6.1.1": [
            "Community members gained improved water access.",
            "Water infrastructure projects implemented.",
            "Potable water coverage increased.",
            "Water harvesting reduced shortages.",
            "Water quality monitoring improved."
        ]
    },

    "SDG_13": {
        "13.2.1": [
            "tCO2e generated during monitoring period.",
            "Emission reductions achieved annually.",
            "Projected lifetime emission reductions.",
            "Carbon sequestration targets over 30 years.",
            "Avoided deforestation reduced baseline emissions."
        ]
    },

    "SDG_15": {
        "15.1.1": [
            "Project area remains forest.",
            "Degraded land restored.",
            "Deforestation avoided.",
            "Area under biodiversity management.",
            "Forest cover monitored via satellite."
        ],

        "15.5.1": [
            "IUCN-listed species recorded.",
            "Threatened species monitored.",
            "Endangered mammals documented.",
            "Biodiversity surveys identified threatened fauna.",
            "Camera traps recorded endangered species."
        ]
    },

    "SDG_17": {
        "17.16.1": [
            "Public-private-community partnership implemented.",
            "Collaboration with local NGOs formalized.",
            "Benefit-sharing agreements signed.",
            "Carbon finance mobilized international investment.",
            "Joint implementation agreements established."
        ]
    }
}