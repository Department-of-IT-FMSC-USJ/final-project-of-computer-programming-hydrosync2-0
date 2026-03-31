def get_simpson_interpretation(sid):
    if sid is None or not isinstance(sid, (int, float)): 
        return {"short": "Not Calculated", "detailed": "No valid data was provided to calculate the index."}
    
    base = "**Simpson's Diversity Index (SID)** measures the probability that two individuals randomly selected from a sample will belong to different species. It factors in both the total number of species (richness) and how equally abundant they are (evenness). "
    
    if sid < 0.2: 
        return {"short": "Very low diversity", "detailed": base + "A score this low means the ecosystem is heavily dominated by one or very few species. This often indicates severe environmental stress, chemical pollution, or a highly artificial environment where only the most resilient organisms survive."}
    elif sid < 0.5: 
        return {"short": "Low diversity", "detailed": base + "There is a noticeable imbalance in the species present. While some variety exists, the ecosystem is likely struggling or in the early stages of recovery from a disturbance."}
    elif sid < 0.7: 
        return {"short": "Moderate diversity", "detailed": base + "The ecosystem is relatively healthy with a good mix of species, though typical natural dominant species might still hold the majority of the population."}
    elif sid <= 1.0: 
        return {"short": "High diversity", "detailed": base + "This indicates a highly stable, healthy, and complex ecosystem with many different thriving species. High diversity systems naturally resist diseases and invasive species better."}
    else: 
        return {"short": "Not defined", "detailed": "Index value falls outside standard ecological bounds."}

def get_pielou_interpretation(e):
    if e is None or not isinstance(e, (int, float)): 
        return {"short": "Not Calculated", "detailed": "No valid data was provided."}
    
    base = "**Pielou's Evenness (J')** measures how evenly individuals are distributed among the different species present, on a scale from 0 to 1. "
    
    if e <= 0.24: 
        return {"short": "Very low evenness", "detailed": base + "One specific species is completely overpopulating the area compared to others. This could be an invasive species or an algal bloom out-competing native life."}
    elif e <= 0.49: 
        return {"short": "Low evenness", "detailed": base + "Certain species are much more dominant than the rest, which can restrict overall biodiversity and indicate mild environmental pressure favoring one type of organism."}
    elif e <= 0.69: 
        return {"short": "Moderate evenness", "detailed": base + "Species populations are fairly balanced. This is a typical, healthy state for standard aquatic environments."}
    elif e <= 0.89: 
        return {"short": "High evenness", "detailed": base + "Most species have very similar population sizes, demonstrating excellent ecological balance and resource sharing."}
    elif e <= 1.00: 
        return {"short": "Very high evenness", "detailed": base + "Perfect or near-perfect population balance across all species. This is a rare sign of pristine ecological health where no single organism dominates."}
    else: 
        return {"short": "Not Defined", "detailed": "Index value falls outside standard ecological bounds."}

def get_richness_interpretation(d):
    if d is None or not isinstance(d, (int, float)): 
        return {"short": "Not Calculated", "detailed": "No valid data was provided."}
    
    base = "**Margalef's Richness Index (d)** focuses purely on the raw variety of distinct species types found in your sample, isolated from total individual count bias. "
    
    if d < 0: 
        return {"short": "Not Defined (Low N)", "detailed": "There were not enough total organisms collected in this sample to mathematically determine the richness."}
    elif d < 2: 
        return {"short": "Low richness", "detailed": base + "Very few distinct species types were found. This lack of variety means the ecosystem has low genetic potential to adapt to changes."}
    elif d <= 3: 
        return {"short": "Moderate richness", "detailed": base + "A normal, mathematically average number of species types exist here. This environment is functioning adequately."}
    elif d <= 5: 
        return {"short": "High richness", "detailed": base + "A very wide variety of distinct species call this environment home. High richness correlates with highly complex food webs."}
    else: 
        return {"short": "Exceptionally high richness", "detailed": base + "This area is a biodiversity hotspot with an incredible variety of distinct life forms, resembling a prime conservation zone."}

def get_plankton_interpretation(abundance):
    if abundance is None or not isinstance(abundance, (int, float)): 
        return {"short": "Not Calculated", "detailed": "No valid data was provided."}
    
    base = "**Plankton Abundance** estimates the total population density of microscopic organisms in a given volume of water. They form the base of the entire aquatic food chain. "
    
    if abundance < 500: 
        return {"short": "Low Abundance", "detailed": base + "This indicates highly transparent, crystal clear water (oligotrophic). However, it also means there is very low nutrient availability to support larger organisms like fish."}
    elif abundance < 2000: 
        return {"short": "Moderate Abundance", "detailed": base + "This is generally the optimal target zone. It provides a balanced, sturdy base for a healthy aquatic food web without compromising water clarity."}
    elif abundance < 5000: 
        return {"short": "High Abundance", "detailed": base + "The water is heavily nutrient-rich (eutrophic). While this can support a massive population of fish, it decreases overall water clarity and starts risking oxygen depletion at night."}
    else: 
        return {"short": "Very High Abundance (Bloom)", "detailed": base + "**Warning:** Potential algal bloom detected! When plankton overpopulate this severely, they block sunlight completely. When they inevitably die, the decomposition process sucks all the oxygen out of the water, often causing mass fish kill events."}
