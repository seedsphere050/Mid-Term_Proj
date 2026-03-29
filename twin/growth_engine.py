# backend/plants/growth_engine.py
"""
Digital Twin Growth Engine
==========================
Per-plant: stage thresholds, ideal conditions, health scoring, recommendations, visual profiles.
Nothing is hardcoded to one value for all plants.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ─────────────────────────────────────────────
# Per-plant stage thresholds (effective days)
# Fast growers (basil, tulsi) reach fully_grown in ~25 days.
# Slow growers (banyan, coffee tree, pineapple) take 100-120 days.
# ─────────────────────────────────────────────
PLANT_STAGE_DAYS: Dict[str, Dict] = {
    'neem':              {'seed':(0,7),'small_plant':(7,30),'medium_plant':(30,90),'fully_grown':(90,float('inf'))},
    'apple':             {'seed':(0,7),'small_plant':(7,30),'medium_plant':(30,90),'fully_grown':(90,float('inf'))},
    'corn':              {'seed':(0,5),'small_plant':(5,20),'medium_plant':(20,45),'fully_grown':(45,float('inf'))},
    'orange':            {'seed':(0,7),'small_plant':(7,30),'medium_plant':(30,80),'fully_grown':(80,float('inf'))},
    'peach':             {'seed':(0,7),'small_plant':(7,25),'medium_plant':(25,60),'fully_grown':(60,float('inf'))},
    'pepper':            {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,40),'fully_grown':(40,float('inf'))},
    'potato':            {'seed':(0,5),'small_plant':(5,20),'medium_plant':(20,45),'fully_grown':(45,float('inf'))},
    'strawberry':        {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,35),'fully_grown':(35,float('inf'))},
    'tomato':            {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,35),'fully_grown':(35,float('inf'))},
    'snake_plant':       {'seed':(0,7),'small_plant':(7,30),'medium_plant':(30,80),'fully_grown':(80,float('inf'))},
    'tulsi':             {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,30),'fully_grown':(30,float('inf'))},
    'aloe_vera':         {'seed':(0,7),'small_plant':(7,25),'medium_plant':(25,60),'fully_grown':(60,float('inf'))},
    'christmas_tree':    {'seed':(0,7),'small_plant':(7,40),'medium_plant':(40,100),'fully_grown':(100,float('inf'))},
    'hibiscus':          {'seed':(0,5),'small_plant':(5,20),'medium_plant':(20,50),'fully_grown':(50,float('inf'))},
    'bougainvillea':     {'seed':(0,7),'small_plant':(7,25),'medium_plant':(25,60),'fully_grown':(60,float('inf'))},
    'lavender':          {'seed':(0,7),'small_plant':(7,21),'medium_plant':(21,45),'fully_grown':(45,float('inf'))},
    'peony':             {'seed':(0,7),'small_plant':(7,25),'medium_plant':(25,55),'fully_grown':(55,float('inf'))},
    'hydrangea':         {'seed':(0,7),'small_plant':(7,21),'medium_plant':(21,50),'fully_grown':(50,float('inf'))},
    'onion':             {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,40),'fully_grown':(40,float('inf'))},
    'garlic':            {'seed':(0,5),'small_plant':(5,20),'medium_plant':(20,45),'fully_grown':(45,float('inf'))},
    'pineapple':         {'seed':(0,7),'small_plant':(7,40),'medium_plant':(40,100),'fully_grown':(100,float('inf'))},
    'oats':              {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,40),'fully_grown':(40,float('inf'))},
    'pot_marigold':      {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,30),'fully_grown':(30,float('inf'))},
    'papaya':            {'seed':(0,5),'small_plant':(5,20),'medium_plant':(20,50),'fully_grown':(50,float('inf'))},
    'blue_cornflower':   {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,30),'fully_grown':(30,float('inf'))},
    'lemon':             {'seed':(0,7),'small_plant':(7,25),'medium_plant':(25,65),'fully_grown':(65,float('inf'))},
    'coffee_tree':       {'seed':(0,7),'small_plant':(7,40),'medium_plant':(40,100),'fully_grown':(100,float('inf'))},
    'wild_carrot':       {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,40),'fully_grown':(40,float('inf'))},
    'snowdrop':          {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,28),'fully_grown':(28,float('inf'))},
    'soyabean':          {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,40),'fully_grown':(40,float('inf'))},
    'english_ivy':       {'seed':(0,7),'small_plant':(7,21),'medium_plant':(21,45),'fully_grown':(45,float('inf'))},
    'hops':              {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,40),'fully_grown':(40,float('inf'))},
    'lotus':             {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,40),'fully_grown':(40,float('inf'))},
    'yarrow':            {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,35),'fully_grown':(35,float('inf'))},
    'feverfew':          {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,30),'fully_grown':(30,float('inf'))},
    'oleander':          {'seed':(0,7),'small_plant':(7,21),'medium_plant':(21,50),'fully_grown':(50,float('inf'))},
    'oregano':           {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,30),'fully_grown':(30,float('inf'))},
    'avocado':           {'seed':(0,7),'small_plant':(7,35),'medium_plant':(35,80),'fully_grown':(80,float('inf'))},
    'beetroot':          {'seed':(0,5),'small_plant':(5,18),'medium_plant':(18,40),'fully_grown':(40,float('inf'))},
    'vervain':           {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,30),'fully_grown':(30,float('inf'))},
    'money_plant':       {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,35),'fully_grown':(35,float('inf'))},
    'banyan':            {'seed':(0,7),'small_plant':(7,45),'medium_plant':(45,120),'fully_grown':(120,float('inf'))},
    'purple_coneflower': {'seed':(0,5),'small_plant':(5,14),'medium_plant':(14,30),'fully_grown':(30,float('inf'))},
    'basil':             {'seed':(0,4),'small_plant':(4,12),'medium_plant':(12,25),'fully_grown':(25,float('inf'))},
    'rose':              {'seed':(0,7),'small_plant':(7,21),'medium_plant':(21,45),'fully_grown':(45,float('inf'))},
}

DEFAULT_STAGE_THRESHOLDS = {'seed':(0,7),'small_plant':(7,21),'medium_plant':(21,45),'fully_grown':(45,float('inf'))}

def get_max_effective_days(plant_type: str) -> float:
    t = PLANT_STAGE_DAYS.get(plant_type, DEFAULT_STAGE_THRESHOLDS)
    fg = t['fully_grown'][0]
    return fg * 1.5 if fg > 0 else 60.0

# ─────────────────────────────────────────────
# Condition score tables
# ─────────────────────────────────────────────
SUNLIGHT_SCORES = {'full_sun':(1.0,'Optimal'),'partial_shade':(0.65,'Adequate'),'low_light':(0.30,'Insufficient')}
WATERING_SCORES = {'daily':(1.0,'Optimal'),'alternate':(0.70,'Adequate'),'weekly':(0.35,'Insufficient')}
SOIL_SCORES     = {'loamy':(1.0,'Ideal'),'sandy':(0.60,'Adequate'),'clay':(0.45,'Poor drainage')}
POT_SCORES      = {'large':(1.0,'Spacious'),'medium':(0.75,'Adequate'),'small':(0.45,'Restrictive')}
ENV_SCORES      = {'outdoor':(1.0,'Natural'),'indoor':(0.80,'Controlled')}
LOCATION_SCORES = {'ground':(1.0,'Best'),'terrace':(0.85,'Good'),'balcony':(0.70,'Limited')}
HEALTH_WEIGHTS  = {'sunlight':0.30,'watering':0.30,'soil':0.25,'pot':0.15}

# ─────────────────────────────────────────────
# Per-plant ideals + specific tip text
# ─────────────────────────────────────────────
PLANT_IDEALS: Dict[str, Dict] = {
    'neem':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Neem needs full sun — place outdoors in direct sunlight.','sunlight_high':'Neem thrives in full sun — no shade needed.','water_low':'Water neem every 2-3 days; it tolerates short dry spells.','water_high':'Reduce watering — neem is drought-tolerant and dislikes wet roots.','soil_wrong':'Neem prefers well-draining loamy or sandy soil.','pot_small':"Use a large pot or ground planting for neem's deep root system."}},
    'apple':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Apple trees need at least 6-8 hours of direct sunlight daily.','sunlight_high':'Full sun is perfect for apples.','water_low':'Water apple trees deeply 2-3 times a week during growing season.','water_high':'Avoid overwatering — apple roots rot in waterlogged soil.','soil_wrong':'Apples prefer deep, well-drained loamy soil.','pot_small':'Apple trees need large containers or ground planting.'}},
    'corn':{'sunlight':'full_sun','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Corn demands full sun — 8+ hours daily for good yield.','sunlight_high':'Great! Corn loves full sun.','water_low':'Corn needs consistent daily watering, especially during tasseling.','water_high':'Current watering is fine — corn is thirsty during summer.','soil_wrong':'Corn grows best in deep, fertile loamy soil.','pot_small':'Corn grows poorly in pots — use ground or raised beds.'}},
    'orange':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Orange trees need full sun for sweet fruit — move to a sunny spot.','sunlight_high':'Full sun is ideal for oranges.','water_low':'Water oranges every 2-3 days; deep watering is better than frequent shallow.','water_high':'Too frequent watering can cause root rot in citrus.','soil_wrong':'Oranges prefer well-drained, slightly acidic loamy soil.','pot_small':'Use a large pot — oranges need room for their deep roots.'}},
    'peach':{'sunlight':'full_sun','watering':'alternate','soil':'sandy','tips':{'sunlight_low':'Peaches need full sun for fruit production — at least 6 hours daily.','sunlight_high':'Perfect — peaches love direct sunlight.','water_low':'Water peach trees deeply twice a week during fruiting season.','water_high':'Reduce watering — peaches prefer slightly dry conditions between watering.','soil_wrong':'Peaches prefer well-draining sandy or loamy soil — they hate wet feet.','pot_small':'Peach trees need large containers or ground planting to thrive.'}},
    'pepper':{'sunlight':'full_sun','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Peppers need full sun — move to your sunniest spot.','sunlight_high':'Full sun is great for pepper production.','water_low':'Peppers need consistent daily watering — uneven watering causes blossom drop.','water_high':'Good — peppers like moist but not waterlogged soil.','soil_wrong':'Peppers prefer rich, well-drained loamy soil.','pot_small':'Use a medium or large pot for better root development.'}},
    'potato':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Potatoes need full sun for good tuber development.','sunlight_high':'Full sun promotes healthy potato growth.','water_low':'Water potatoes every 2-3 days — consistent moisture prevents hollow tubers.','water_high':'Avoid overwatering — excess moisture causes tuber rot.','soil_wrong':'Potatoes prefer loose, well-drained loamy soil for tuber expansion.','pot_small':'Use a large deep pot or grow bag for potato cultivation.'}},
    'strawberry':{'sunlight':'full_sun','watering':'daily','soil':'sandy','tips':{'sunlight_low':'Strawberries need 8+ hours of sun for sweet berries.','sunlight_high':'Full sun is perfect for strawberries.','water_low':'Keep strawberry soil consistently moist — daily watering is ideal.','water_high':'Good — strawberries like regular watering, especially during fruiting.','soil_wrong':'Strawberries prefer well-drained sandy or sandy-loam soil.','pot_small':'Small pots limit strawberry runners — use medium or hanging baskets.'}},
    'tomato':{'sunlight':'full_sun','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Tomatoes need full sun — move to get 8+ hours of direct light.','sunlight_high':'Full sun is perfect for tomatoes.','water_low':'Water tomatoes daily — irregular watering causes blossom end rot.','water_high':'Good — tomatoes need consistent moisture, especially during fruiting.','soil_wrong':'Tomatoes prefer rich, well-drained loamy soil.','pot_small':'Use at least a 12-inch pot for tomatoes — small pots stunt growth.'}},
    'snake_plant':{'sunlight':'partial_shade','watering':'weekly','soil':'sandy','tips':{'sunlight_low':'Snake plant tolerates low light but grows faster in indirect bright light.','sunlight_high':'Too much direct sun scorches snake plant leaves — provide indirect light.','water_low':'Snake plant prefers weekly watering — it stores water in its leaves.','water_high':"You're overwatering! Snake plant rots easily — water only when soil is dry.",'soil_wrong':'Snake plant needs fast-draining sandy or cactus mix soil.','pot_small':'Snake plant can handle small pots but prefers medium for root health.'}},
    'tulsi':{'sunlight':'full_sun','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Tulsi (Holy Basil) needs full sun — at least 6 hours daily.','sunlight_high':'Full sun is perfect for tulsi.','water_low':"Water tulsi daily — it wilts quickly in heat without moisture.",'water_high':'Good — tulsi likes moist soil, especially in summer.','soil_wrong':'Tulsi thrives in rich, well-drained loamy soil.','pot_small':'Use a medium to large pot to allow tulsi to bush out fully.'}},
    'aloe_vera':{'sunlight':'full_sun','watering':'weekly','soil':'sandy','tips':{'sunlight_low':'Aloe vera needs bright indirect to direct light — move to a sunnier spot.','sunlight_high':"Full sun is great for aloe — it's a desert plant!",'water_low':'Aloe only needs weekly watering — wait until soil is completely dry.','water_high':"Critical: you're overwatering! Aloe root rot is the #1 cause of death.",'soil_wrong':'Aloe vera must have sandy or cactus mix soil — never keep it in clay.','pot_small':'Aloe grows pups — use a wider medium pot to allow offsets.'}},
    'christmas_tree':{'sunlight':'partial_shade','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Christmas trees prefer bright indirect light or dappled shade.','sunlight_high':'Protect from intense afternoon sun — partial shade is ideal.','water_low':'Water every 2-3 days — keep the root ball moist.','water_high':'Good moisture is fine — just ensure good drainage.','soil_wrong':'Use well-drained, slightly acidic loamy soil.','pot_small':'Use a large container — Christmas trees have extensive root systems.'}},
    'hibiscus':{'sunlight':'full_sun','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Hibiscus needs full sun for prolific blooming.','sunlight_high':'Perfect — hibiscus thrives in full sun.','water_low':"Water hibiscus daily during growing season — it's thirsty!",'water_high':'Good — hibiscus loves water, especially in summer heat.','soil_wrong':'Hibiscus prefers fertile, well-drained loamy soil.','pot_small':'Use a large pot — hibiscus becomes a sizable shrub.'}},
    'bougainvillea':{'sunlight':'full_sun','watering':'alternate','soil':'sandy','tips':{'sunlight_low':"Bougainvillea MUST have full sun — it won't flower in shade.",'sunlight_high':"Full sun is essential for bougainvillea's vibrant blooms.",'water_low':'Water every 2-3 days — slight drought stress actually triggers flowering.','water_high':'Reduce watering — overwatering causes leaf growth over flowers.','soil_wrong':'Bougainvillea prefers well-drained sandy soil — avoid heavy clay.','pot_small':'Use a large pot and provide a trellis for climbing support.'}},
    'lavender':{'sunlight':'full_sun','watering':'weekly','soil':'sandy','tips':{'sunlight_low':'Lavender needs full sun — 6+ hours minimum for good fragrance and blooms.','sunlight_high':'Full sun is perfect for lavender.','water_low':'Lavender is drought-tolerant — weekly watering once established.','water_high':'Reduce watering! Lavender hates wet roots and will rot.','soil_wrong':'Lavender must have well-drained sandy or gravelly soil.','pot_small':'Use a medium terracotta pot with drainage holes for lavender.'}},
    'peony':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Peonies need full sun for blooming — at least 6 hours daily.','sunlight_high':'Full sun is ideal for peonies.','water_low':'Water peonies every 2-3 days during growing season.','water_high':'Avoid overwatering — peonies dislike soggy soil.','soil_wrong':'Peonies prefer deep, fertile, well-drained loamy soil.','pot_small':'Peonies need large, deep pots or ground planting.'}},
    'hydrangea':{'sunlight':'partial_shade','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Hydrangeas prefer morning sun and afternoon shade — bright indirect light is ideal.','sunlight_high':'Too much direct afternoon sun scorches hydrangea leaves.','water_low':'Hydrangeas need daily watering — they wilt dramatically when dry.','water_high':'Good — hydrangeas love moisture; water consistently.','soil_wrong':'Hydrangeas prefer moist, rich, well-drained loamy soil.','pot_small':'Use a large pot — hydrangeas grow into substantial shrubs.'}},
    'onion':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Onions need full sun — poor light gives small, poor quality bulbs.','sunlight_high':'Full sun is perfect for onion bulb development.','water_low':'Water every 2-3 days; reduce watering as bulbs mature.','water_high':'Avoid overwatering — wet soil causes onion bulb rot.','soil_wrong':'Onions prefer loose, well-drained, fertile loamy soil.','pot_small':'Use a wide, shallow container for onions.'}},
    'garlic':{'sunlight':'full_sun','watering':'weekly','soil':'loamy','tips':{'sunlight_low':'Garlic needs full sun for bulb development.','sunlight_high':'Full sun is ideal for garlic.','water_low':'Garlic needs weekly deep watering — reduce near harvest.','water_high':'Reduce watering — garlic prefers drying out between watering.','soil_wrong':'Garlic grows best in well-drained, fertile loamy soil.','pot_small':'Use a medium to large pot that is at least 8 inches deep.'}},
    'pineapple':{'sunlight':'full_sun','watering':'alternate','soil':'sandy','tips':{'sunlight_low':'Pineapple needs full sun — minimum 6 hours of direct light.','sunlight_high':'Full sun is perfect for pineapples.','water_low':'Water every 2-3 days; the crown collects water naturally.','water_high':'Reduce watering — pineapple is drought-tolerant and rots easily.','soil_wrong':'Pineapple needs very well-drained, slightly acidic sandy soil.','pot_small':'Use a large pot — pineapple plants spread significantly.'}},
    'oats':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Oats need full sun for good grain development.','sunlight_high':'Full sun is ideal for oats.','water_low':'Water oats regularly — every 2-3 days during growth.','water_high':'Adequate watering — oats prefer moist but not waterlogged soil.','soil_wrong':'Oats grow best in fertile, well-drained loamy soil.','pot_small':'Oats can be grown in medium containers or raised beds.'}},
    'pot_marigold':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Pot marigold (Calendula) needs full sun for prolific blooming.','sunlight_high':'Full sun is perfect for marigolds.','water_low':'Water every 2-3 days — marigolds are somewhat drought tolerant.','water_high':'Avoid overwatering — marigolds are prone to mildew in wet conditions.','soil_wrong':'Marigolds prefer moderately fertile, well-drained loamy soil.','pot_small':'Small to medium pots work fine for marigolds.'}},
    'papaya':{'sunlight':'full_sun','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Papaya needs full sun — inadequate light reduces fruit quality.','sunlight_high':'Full sun is excellent for papaya growth.','water_low':"Papaya needs regular daily watering — it's a fast-growing tropical.",'water_high':'Good — papaya likes moisture but ensure drainage to prevent root rot.','soil_wrong':'Papaya requires rich, well-drained loamy soil.','pot_small':'Papaya becomes a large plant — use the biggest pot possible.'}},
    'blue_cornflower':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Cornflowers need full sun for best flowering.','sunlight_high':'Full sun is ideal for cornflowers.','water_low':'Water every 2-3 days — cornflowers are drought-tolerant once established.','water_high':'Reduce watering — cornflowers prefer drier conditions.','soil_wrong':'Cornflowers prefer well-drained, moderately fertile loamy soil.','pot_small':'Medium pots work well for cornflowers.'}},
    'lemon':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Lemon trees need 8+ hours of full sun for good fruit production.','sunlight_high':'Full sun is perfect for lemon trees.','water_low':'Water deeply every 2-3 days — allow top inch of soil to dry.','water_high':'Avoid overwatering — lemon tree roots rot in soggy soil.','soil_wrong':'Lemons prefer well-drained, slightly acidic loamy soil.','pot_small':'Use a large pot (20L+) for lemon trees.'}},
    'coffee_tree':{'sunlight':'partial_shade','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Coffee prefers bright indirect light or filtered sun — avoid harsh afternoon sun.','sunlight_high':'Too much direct sun scorches coffee leaves — provide afternoon shade.','water_low':'Water coffee trees every 2-3 days — keep soil consistently moist.','water_high':'Good moisture, but ensure drainage — coffee hates waterlogged roots.','soil_wrong':'Coffee prefers slightly acidic, well-drained loamy soil.','pot_small':'Use a large pot — coffee trees grow to 1.5-2m in containers.'}},
    'wild_carrot':{'sunlight':'full_sun','watering':'alternate','soil':'sandy','tips':{'sunlight_low':'Wild carrot needs full sun for good taproot development.','sunlight_high':'Full sun is ideal for wild carrot.','water_low':'Water every 2-3 days — consistent moisture prevents forked roots.','water_high':'Reduce watering — carrots prefer slightly dry conditions between watering.','soil_wrong':'Carrots need loose, deep, sandy soil — heavy soil causes misshapen roots.','pot_small':'Use a deep container — carrots need at least 12 inches depth.'}},
    'snowdrop':{'sunlight':'partial_shade','watering':'alternate','soil':'loamy','tips':{'sunlight_low':"Snowdrops prefer dappled shade or light — they're woodland plants.",'sunlight_high':'Protect snowdrops from direct afternoon sun.','water_low':'Water every 2-3 days during growth; reduce after flowering.','water_high':'Moderate watering is fine — ensure good drainage.','soil_wrong':'Snowdrops prefer moist, humus-rich, well-drained loamy soil.','pot_small':'Small to medium pots work well for snowdrops.'}},
    'soyabean':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Soybeans need full sun — poor light reduces pod yield significantly.','sunlight_high':'Full sun is perfect for soybeans.','water_low':'Water every 2-3 days — especially important during pod fill.','water_high':'Avoid overwatering — soybeans are drought-tolerant once established.','soil_wrong':'Soybeans prefer fertile, well-drained loamy soil.','pot_small':'Use medium to large containers for soybeans.'}},
    'english_ivy':{'sunlight':'partial_shade','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'English ivy tolerates low light but grows faster in bright indirect light.','sunlight_high':'Too much direct sun bleaches ivy leaves — bright indirect light is ideal.','water_low':'Water ivy every 2-3 days — keep the soil evenly moist.','water_high':'Reduce watering — ivy is prone to root rot in wet soil.','soil_wrong':'Ivy prefers well-drained, fertile loamy soil.','pot_small':'Medium pots work for ivy — use a hanging basket for trailing effect.'}},
    'hops':{'sunlight':'full_sun','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Hops are vigorous climbers that need full sun for good cone production.','sunlight_high':'Full sun is essential for hops.','water_low':'Hops need consistent daily watering during their rapid growth phase.','water_high':'Good — hops are heavy drinkers, especially in summer.','soil_wrong':'Hops prefer deep, rich, well-drained loamy soil.','pot_small':'Hops grow very large — use the largest container possible with a tall trellis.'}},
    'lotus':{'sunlight':'full_sun','watering':'daily','soil':'clay','tips':{'sunlight_low':'Lotus needs full sun — minimum 5-6 hours for flowering.','sunlight_high':'Full sun is perfect for lotus.','water_low':'Lotus is an aquatic plant — it must always be in standing water.','water_high':'Good — lotus grows in water; maintain 15-30cm water depth.','soil_wrong':'Lotus needs heavy clay soil at the bottom of a water pot — not normal potting mix.','pot_small':'Use a wide, shallow container filled with water — minimum 40cm diameter.'}},
    'yarrow':{'sunlight':'full_sun','watering':'weekly','soil':'sandy','tips':{'sunlight_low':"Yarrow needs full sun — it's a meadow plant.",'sunlight_high':'Full sun is ideal for yarrow.','water_low':'Yarrow is drought-tolerant — weekly watering once established.','water_high':'Reduce watering — yarrow tolerates poor, dry conditions.','soil_wrong':'Yarrow thrives in well-drained, even poor sandy soil.','pot_small':'Medium pots work for yarrow.'}},
    'feverfew':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Feverfew needs full sun for best flowering and medicinal potency.','sunlight_high':'Full sun is great for feverfew.','water_low':'Water every 2-3 days — feverfew is moderately drought-tolerant.','water_high':'Avoid overwatering — feverfew prefers slightly dry conditions.','soil_wrong':'Feverfew grows well in well-drained, moderately fertile loamy soil.','pot_small':'Medium pots work well for feverfew.'}},
    'oleander':{'sunlight':'full_sun','watering':'alternate','soil':'sandy','tips':{'sunlight_low':'Oleander needs full sun to bloom well.','sunlight_high':'Full sun is perfect for oleander.','water_low':'Water every 2-3 days; oleander is drought-tolerant once established.','water_high':'Reduce watering — oleander is highly drought-tolerant.','soil_wrong':'Oleander prefers well-drained sandy or loamy soil.','pot_small':'Use a large pot — oleander can become a large shrub.'}},
    'oregano':{'sunlight':'full_sun','watering':'weekly','soil':'sandy','tips':{'sunlight_low':"Oregano needs full sun for the best flavour and aroma.",'sunlight_high':"Full sun intensifies oregano's essential oils — perfect!",'water_low':"Oregano prefers dry conditions — weekly watering is plenty.",'water_high':'Reduce watering! Oregano dislikes wet roots — water only when soil is dry.','soil_wrong':'Oregano grows best in well-drained sandy or gravelly soil.','pot_small':'Small to medium terracotta pots are ideal for oregano.'}},
    'avocado':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Avocado trees need full sun — at least 6 hours for healthy growth.','sunlight_high':'Full sun is ideal for avocado.','water_low':'Water deeply every 2-3 days — avocado roots go deep.','water_high':'Reduce watering — avocado is very sensitive to root rot from overwatering.','soil_wrong':'Avocado needs well-drained loamy soil with excellent aeration.','pot_small':'Use the largest pot you have — avocado trees grow very large.'}},
    'beetroot':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Beetroot needs full sun for good root development.','sunlight_high':'Full sun is great for beetroot.','water_low':'Water every 2-3 days — consistent moisture prevents tough, woody beets.','water_high':'Moderate watering is fine — avoid waterlogging.','soil_wrong':'Beetroot needs loose, well-drained loamy soil for root expansion.','pot_small':'Use a deep container — beetroot needs at least 12 inches depth.'}},
    'vervain':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Vervain needs full sun for prolific flowering.','sunlight_high':'Full sun is ideal for vervain.','water_low':'Water every 2-3 days — vervain is moderately drought-tolerant.','water_high':'Reduce watering — vervain prefers slightly dry soil between watering.','soil_wrong':'Vervain grows well in well-drained, average fertility loamy soil.','pot_small':'Medium pots work for vervain.'}},
    'money_plant':{'sunlight':'partial_shade','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Money plant tolerates low light but grows faster in bright indirect light.','sunlight_high':'Move away from direct sun — money plant leaves scorch easily.','water_low':'Water every 2-3 days — money plant likes moderately moist soil.','water_high':'Reduce watering — overwatering causes yellowing leaves.','soil_wrong':'Money plant grows well in well-drained loamy or potting mix.','pot_small':'Money plant is adaptable — medium pots with a support pole work well.'}},
    'banyan':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':"Banyan trees need full sun to develop their iconic aerial roots.",'sunlight_high':"Full sun is natural for banyan — it's a tropical tree.",'water_low':'Water deeply every 2-3 days when young; mature banyans are drought-tolerant.','water_high':'Moderate watering is fine for banyan.','soil_wrong':'Banyan prefers deep, well-drained loamy soil.','pot_small':'Banyan grows enormous — only suitable for very large containers or ground.'}},
    'purple_coneflower':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Purple coneflower (Echinacea) needs full sun for prolific blooming.','sunlight_high':'Full sun is perfect for Echinacea.','water_low':'Water every 2-3 days when young; established plants are drought-tolerant.','water_high':'Reduce watering — Echinacea prefers drier conditions once established.','soil_wrong':'Purple coneflower prefers well-drained, average fertility loamy soil.','pot_small':'Medium to large pots work for coneflowers.'}},
    'basil':{'sunlight':'full_sun','watering':'daily','soil':'loamy','tips':{'sunlight_low':'Basil needs at least 6 hours of direct sun for flavourful leaves.','sunlight_high':'Full sun is perfect for basil.','water_low':'Basil needs daily watering — it wilts quickly and that stresses the plant.','water_high':'Good — basil loves consistent moisture, especially in hot weather.','soil_wrong':'Basil prefers rich, well-drained loamy soil.','pot_small':'Use a medium pot — basil needs room to bush out.'}},
    'rose':{'sunlight':'full_sun','watering':'alternate','soil':'loamy','tips':{'sunlight_low':'Roses need at least 6 hours of full sun — less sun means fewer blooms.','sunlight_high':'Full sun is ideal for roses.','water_low':'Water roses deeply every 2-3 days — they are heavy feeders.','water_high':'Avoid overwatering — water at the base to prevent fungal disease.','soil_wrong':'Roses prefer rich, well-drained loamy soil with good organic matter.','pot_small':'Use a large, deep pot for roses — they have extensive root systems.'}},
}

# Plants that have actual stage3 GLB files (42 total)
PLANTS_WITH_GLB = {
    'neem','apple','corn','orange','peach','pepper','potato','strawberry',
    'tomato','snake_plant','tulsi','aloe_vera','christmas_tree','hibiscus',
    'bougainvillea','lavender','peony','hydrangea','onion','garlic',
    'pineapple','oats','pot_marigold','papaya','blue_cornflower','lemon',
    'coffee_tree','wild_carrot','snowdrop','soyabean','english_ivy','hops',
    'lotus','yarrow','feverfew','oleander','oregano','avocado','beetroot',
    'vervain','money_plant','banyan',
}

PLANT_VISUAL_PROFILES: Dict[str, Dict] = {
    'neem':{'primary':'#2E7D32','secondary':'#1B5E20','accent':'#A5D6A7','shape':'tree'},
    'apple':{'primary':'#388E3C','secondary':'#1B5E20','accent':'#F44336','shape':'tree'},
    'corn':{'primary':'#8BC34A','secondary':'#558B2F','accent':'#FFC107','shape':'tall'},
    'orange':{'primary':'#388E3C','secondary':'#2E7D32','accent':'#FF9800','shape':'tree'},
    'peach':{'primary':'#388E3C','secondary':'#1B5E20','accent':'#FF8A65','shape':'tree'},
    'pepper':{'primary':'#43A047','secondary':'#2E7D32','accent':'#E53935','shape':'bushy'},
    'potato':{'primary':'#558B2F','secondary':'#33691E','accent':'#A1887F','shape':'bushy'},
    'strawberry':{'primary':'#43A047','secondary':'#2E7D32','accent':'#E53935','shape':'bushy'},
    'tomato':{'primary':'#388E3C','secondary':'#1B5E20','accent':'#F44336','shape':'vine'},
    'snake_plant':{'primary':'#2E7D32','secondary':'#1A237E','accent':'#F9A825','shape':'rosette'},
    'tulsi':{'primary':'#388E3C','secondary':'#1B5E20','accent':'#A5D6A7','shape':'bushy'},
    'aloe_vera':{'primary':'#4CAF50','secondary':'#2E7D32','accent':'#81C784','shape':'rosette'},
    'christmas_tree':{'primary':'#1B5E20','secondary':'#003300','accent':'#F44336','shape':'tree'},
    'hibiscus':{'primary':'#43A047','secondary':'#2E7D32','accent':'#E91E63','shape':'shrub'},
    'bougainvillea':{'primary':'#558B2F','secondary':'#33691E','accent':'#E91E63','shape':'vine'},
    'lavender':{'primary':'#7E57C2','secondary':'#512DA8','accent':'#CE93D8','shape':'bushy'},
    'peony':{'primary':'#43A047','secondary':'#2E7D32','accent':'#F48FB1','shape':'bushy'},
    'hydrangea':{'primary':'#43A047','secondary':'#2E7D32','accent':'#90CAF9','shape':'shrub'},
    'onion':{'primary':'#8BC34A','secondary':'#558B2F','accent':'#CE93D8','shape':'bushy'},
    'garlic':{'primary':'#8BC34A','secondary':'#558B2F','accent':'#FFFFFF','shape':'bushy'},
    'pineapple':{'primary':'#8BC34A','secondary':'#558B2F','accent':'#FFD600','shape':'rosette'},
    'oats':{'primary':'#AED581','secondary':'#8BC34A','accent':'#F9A825','shape':'tall'},
    'pot_marigold':{'primary':'#558B2F','secondary':'#33691E','accent':'#FF9800','shape':'bushy'},
    'papaya':{'primary':'#388E3C','secondary':'#1B5E20','accent':'#FF9800','shape':'tall'},
    'blue_cornflower':{'primary':'#43A047','secondary':'#2E7D32','accent':'#42A5F5','shape':'tall'},
    'lemon':{'primary':'#388E3C','secondary':'#2E7D32','accent':'#FFD600','shape':'tree'},
    'coffee_tree':{'primary':'#2E7D32','secondary':'#1B5E20','accent':'#A1887F','shape':'shrub'},
    'wild_carrot':{'primary':'#8BC34A','secondary':'#558B2F','accent':'#FFFFFF','shape':'bushy'},
    'snowdrop':{'primary':'#81C784','secondary':'#43A047','accent':'#FFFFFF','shape':'bushy'},
    'soyabean':{'primary':'#8BC34A','secondary':'#558B2F','accent':'#F9A825','shape':'bushy'},
    'english_ivy':{'primary':'#388E3C','secondary':'#1B5E20','accent':'#A5D6A7','shape':'vine'},
    'hops':{'primary':'#8BC34A','secondary':'#558B2F','accent':'#A5D6A7','shape':'vine'},
    'lotus':{'primary':'#43A047','secondary':'#2E7D32','accent':'#F48FB1','shape':'rosette'},
    'yarrow':{'primary':'#AED581','secondary':'#8BC34A','accent':'#FFFFFF','shape':'bushy'},
    'feverfew':{'primary':'#8BC34A','secondary':'#558B2F','accent':'#FFFFFF','shape':'bushy'},
    'oleander':{'primary':'#43A047','secondary':'#2E7D32','accent':'#F48FB1','shape':'shrub'},
    'oregano':{'primary':'#558B2F','secondary':'#33691E','accent':'#CE93D8','shape':'bushy'},
    'avocado':{'primary':'#2E7D32','secondary':'#1B5E20','accent':'#558B2F','shape':'tree'},
    'beetroot':{'primary':'#558B2F','secondary':'#33691E','accent':'#880E4F','shape':'bushy'},
    'vervain':{'primary':'#558B2F','secondary':'#33691E','accent':'#9575CD','shape':'bushy'},
    'money_plant':{'primary':'#66BB6A','secondary':'#2E7D32','accent':'#F9A825','shape':'vine'},
    'banyan':{'primary':'#2E7D32','secondary':'#1A237E','accent':'#A5D6A7','shape':'tree'},
    'purple_coneflower':{'primary':'#558B2F','secondary':'#33691E','accent':'#9C27B0','shape':'tall'},
    'basil':{'primary':'#43A047','secondary':'#2E7D32','accent':'#A5D6A7','shape':'bushy'},
    'rose':{'primary':'#43A047','secondary':'#1B5E20','accent':'#E91E63','shape':'shrub'},
}


@dataclass
class GrowthResult:
    stage: str
    health_score: float
    effective_days: float
    real_days: float
    growth_percentage: float
    growth_multiplier: float
    stage_progress: float
    days_to_next_stage: float
    condition_scores: Dict[str, float]
    condition_labels: Dict[str, str]
    recommendations: List[str]
    visual_profile: Dict[str, str]
    stage_label: str
    health_label: str
    health_color: str


def compute_growth_multiplier(sunlight, watering, soil, pot, environment, location):
    s = SUNLIGHT_SCORES.get(sunlight, (0.5,''))[0]
    w = WATERING_SCORES.get(watering, (0.5,''))[0]
    o = SOIL_SCORES.get(soil,        (0.5,''))[0]
    p = POT_SCORES.get(pot,          (0.5,''))[0]
    e = ENV_SCORES.get(environment,  (0.9,''))[0]
    l = LOCATION_SCORES.get(location,(0.85,''))[0]
    base = s*0.28 + w*0.28 + o*0.22 + p*0.12 + e*0.05 + l*0.05
    return round(0.15 + base*1.35, 3)


def compute_health_score(sunlight, watering, soil, pot, plant_type):
    ideals = PLANT_IDEALS.get(plant_type, {})
    ideal_sun  = ideals.get('sunlight', 'full_sun')
    ideal_wat  = ideals.get('watering', 'alternate')
    ideal_soil = ideals.get('soil', 'loamy')

    raw = {
        'sunlight': SUNLIGHT_SCORES.get(sunlight, (0.5,'Unknown'))[0],
        'watering': WATERING_SCORES.get(watering, (0.5,'Unknown'))[0],
        'soil':     SOIL_SCORES.get(soil,         (0.5,'Unknown'))[0],
        'pot':      POT_SCORES.get(pot,            (0.5,'Unknown'))[0],
    }
    labels = {
        'sunlight': SUNLIGHT_SCORES.get(sunlight, (0.5,'Unknown'))[1],
        'watering': WATERING_SCORES.get(watering, (0.5,'Unknown'))[1],
        'soil':     SOIL_SCORES.get(soil,         (0.5,'Unknown'))[1],
        'pot':      POT_SCORES.get(pot,            (0.5,'Unknown'))[1],
    }
    ideal_sun_score  = SUNLIGHT_SCORES.get(ideal_sun,  (1.0,''))[0]
    ideal_wat_score  = WATERING_SCORES.get(ideal_wat,  (1.0,''))[0]
    ideal_soil_score = SOIL_SCORES.get(ideal_soil,     (1.0,''))[0]

    adjusted = {
        'sunlight': 1.0 - abs(raw['sunlight'] - ideal_sun_score),
        'watering': 1.0 - abs(raw['watering'] - ideal_wat_score),
        'soil':     1.0 - abs(raw['soil']     - ideal_soil_score),
        'pot':      raw['pot'],
    }
    health = sum(adjusted[k] * HEALTH_WEIGHTS[k] for k in adjusted) * 100
    return round(health, 2), adjusted, labels


def determine_stage(effective_days, plant_type):
    labels = {'seed':'🌱 Seed','small_plant':'🌿 Small Plant','medium_plant':'🪴 Medium Plant','fully_grown':'🌳 Fully Grown'}
    thresholds = PLANT_STAGE_DAYS.get(plant_type, DEFAULT_STAGE_THRESHOLDS)
    for stage, (low, high) in thresholds.items():
        if low <= effective_days < high:
            if high == float('inf'):
                return stage, labels[stage], 1.0, 0
            prog = (effective_days - low) / (high - low)
            return stage, labels[stage], round(prog, 3), round(high - effective_days, 1)
    return 'fully_grown', labels['fully_grown'], 1.0, 0


def get_health_label(score):
    if score >= 80: return '🟢 Thriving', '#22C55E'
    if score >= 60: return '🟡 Healthy',  '#EAB308'
    if score >= 40: return '🟠 Stressed', '#F97316'
    return '🔴 Critical', '#EF4444'


def generate_recommendations(plant_type, sunlight, watering, soil, pot):
    recs   = []
    ideals = PLANT_IDEALS.get(plant_type, {})
    tips   = ideals.get('tips', {})
    ideal_sun  = ideals.get('sunlight', 'full_sun')
    ideal_wat  = ideals.get('watering', 'alternate')
    ideal_soil = ideals.get('soil', 'loamy')

    if sunlight != ideal_sun:
        if ideal_sun == 'full_sun' and sunlight in ('partial_shade','low_light'):
            recs.append(f"☀️ {tips.get('sunlight_low', 'Move to a sunnier spot.')}")
        elif ideal_sun in ('partial_shade','low_light') and sunlight == 'full_sun':
            recs.append(f"🌤️ {tips.get('sunlight_high', 'Provide some shade.')}")

    if watering != ideal_wat:
        if ideal_wat == 'daily' and watering in ('alternate','weekly'):
            recs.append(f"💧 {tips.get('water_low', 'Water more frequently.')}")
        elif ideal_wat == 'weekly' and watering in ('daily','alternate'):
            recs.append(f"💧 {tips.get('water_high', 'Reduce watering frequency.')}")
        elif ideal_wat == 'alternate' and watering == 'weekly':
            recs.append(f"💧 {tips.get('water_low', 'Water a little more frequently.')}")
        elif ideal_wat == 'alternate' and watering == 'daily':
            recs.append(f"💧 {tips.get('water_high', 'Slightly reduce watering.')}")

    if soil != ideal_soil:
        recs.append(f"🌍 {tips.get('soil_wrong', f'Consider {ideal_soil} soil.')}")

    if pot == 'small':
        recs.append(f"🪴 {tips.get('pot_small', 'Upgrade to a larger pot.')}")

    if not recs:
        recs.append("✅ Your care conditions are ideal for this plant. Keep it up!")

    return recs


def simulate_growth(plant_type, real_days, sunlight, watering, soil, pot,
                    environment='outdoor', location='ground'):
    multiplier     = compute_growth_multiplier(sunlight, watering, soil, pot, environment, location)
    effective_days = real_days * multiplier
    health_score, condition_scores, condition_labels = compute_health_score(
        sunlight, watering, soil, pot, plant_type)
    stage, stage_label, stage_progress, days_to_next = determine_stage(effective_days, plant_type)
    max_days   = get_max_effective_days(plant_type)
    growth_pct = min(100.0, (effective_days / max_days) * 100)
    health_label, health_color = get_health_label(health_score)
    recommendations = generate_recommendations(plant_type, sunlight, watering, soil, pot)
    visual_profile  = PLANT_VISUAL_PROFILES.get(plant_type,
        {'primary':'#4CAF50','secondary':'#2E7D32','accent':'#81C784','shape':'generic'})

    return GrowthResult(
        stage=stage, health_score=round(health_score,2),
        effective_days=round(effective_days,2), real_days=round(real_days,2),
        growth_percentage=round(growth_pct,1), growth_multiplier=multiplier,
        stage_progress=stage_progress, days_to_next_stage=days_to_next,
        condition_scores=condition_scores, condition_labels=condition_labels,
        recommendations=recommendations, visual_profile=visual_profile,
        stage_label=stage_label, health_label=health_label, health_color=health_color,
    )
