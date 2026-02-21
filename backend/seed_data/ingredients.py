"""
Comprehensive ingredient seed data for meal planning system.

This file contains 100+ common Indian ingredients with:
- Nutritional information per 100g
- Category classification
- Allergen information
- Typical measurement units
"""

# Vegetables
VEGETABLES = [
    {
        'name': 'onion',
        'name_hindi': 'प्याज',
        'category': 'vegetable',
        'calories_per_100g': 40,
        'protein_per_100g': 1.1,
        'carbs_per_100g': 9.3,
        'fats_per_100g': 0.1,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'tomato',
        'name_hindi': 'टमाटर',
        'category': 'vegetable',
        'calories_per_100g': 18,
        'protein_per_100g': 0.9,
        'carbs_per_100g': 3.9,
        'fats_per_100g': 0.2,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'potato',
        'name_hindi': 'आलू',
        'category': 'vegetable',
        'calories_per_100g': 77,
        'protein_per_100g': 2.0,
        'carbs_per_100g': 17.5,
        'fats_per_100g': 0.1,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'carrot',
        'name_hindi': 'गाजर',
        'category': 'vegetable',
        'calories_per_100g': 41,
        'protein_per_100g': 0.9,
        'carbs_per_100g': 9.6,
        'fats_per_100g': 0.2,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'cucumber',
        'name_hindi': 'खीरा',
        'category': 'vegetable',
        'calories_per_100g': 15,
        'protein_per_100g': 0.7,
        'carbs_per_100g': 3.6,
        'fats_per_100g': 0.1,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'peas',
        'name_hindi': 'मटर',
        'category': 'vegetable',
        'calories_per_100g': 81,
        'protein_per_100g': 5.4,
        'carbs_per_100g': 14.5,
        'fats_per_100g': 0.4,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'green_chili',
        'name_hindi': 'हरी मिर्च',
        'category': 'vegetable',
        'calories_per_100g': 40,
        'protein_per_100g': 1.9,
        'carbs_per_100g': 9.5,
        'fats_per_100g': 0.2,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'coriander_leaves',
        'name_hindi': 'धनिया पत्ती',
        'category': 'vegetable',
        'calories_per_100g': 23,
        'protein_per_100g': 2.1,
        'carbs_per_100g': 3.7,
        'fats_per_100g': 0.5,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'spinach',
        'name_hindi': 'पालक',
        'category': 'vegetable',
        'calories_per_100g': 23,
        'protein_per_100g': 2.9,
        'carbs_per_100g': 3.6,
        'fats_per_100g': 0.4,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'cauliflower',
        'name_hindi': 'फूलगोभी',
        'category': 'vegetable',
        'calories_per_100g': 25,
        'protein_per_100g': 1.9,
        'carbs_per_100g': 5.0,
        'fats_per_100g': 0.3,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'cabbage',
        'name_hindi': 'पत्तागोभी',
        'category': 'vegetable',
        'calories_per_100g': 25,
        'protein_per_100g': 1.3,
        'carbs_per_100g': 5.8,
        'fats_per_100g': 0.1,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'bell_pepper',
        'name_hindi': 'शिमला मिर्च',
        'category': 'vegetable',
        'calories_per_100g': 31,
        'protein_per_100g': 1.0,
        'carbs_per_100g': 6.0,
        'fats_per_100g': 0.3,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'broccoli',
        'name_hindi': 'ब्रोकली',
        'category': 'vegetable',
        'calories_per_100g': 34,
        'protein_per_100g': 2.8,
        'carbs_per_100g': 7.0,
        'fats_per_100g': 0.4,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'drumstick',
        'name_hindi': 'सहजन',
        'category': 'vegetable',
        'calories_per_100g': 37,
        'protein_per_100g': 2.1,
        'carbs_per_100g': 8.5,
        'fats_per_100g': 0.2,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'fenugreek_leaves',
        'name_hindi': 'मेथी',
        'category': 'vegetable',
        'calories_per_100g': 49,
        'protein_per_100g': 4.4,
        'carbs_per_100g': 6.0,
        'fats_per_100g': 0.9,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'mixed_vegetables',
        'name_hindi': 'मिक्स सब्जी',
        'category': 'vegetable',
        'calories_per_100g': 50,
        'protein_per_100g': 2.5,
        'carbs_per_100g': 10.0,
        'fats_per_100g': 0.3,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
]

# Fruits
FRUITS = [
    {
        'name': 'banana',
        'name_hindi': 'केला',
        'category': 'fruit',
        'calories_per_100g': 89,
        'protein_per_100g': 1.1,
        'carbs_per_100g': 22.8,
        'fats_per_100g': 0.3,
        'typical_unit': 'piece',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'apple',
        'name_hindi': 'सेब',
        'category': 'fruit',
        'calories_per_100g': 52,
        'protein_per_100g': 0.3,
        'carbs_per_100g': 13.8,
        'fats_per_100g': 0.2,
        'typical_unit': 'piece',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'mixed_berries',
        'name_hindi': 'बेरीज',
        'category': 'fruit',
        'calories_per_100g': 57,
        'protein_per_100g': 0.7,
        'carbs_per_100g': 14.5,
        'fats_per_100g': 0.3,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'coconut',
        'name_hindi': 'नारियल',
        'category': 'fruit',
        'calories_per_100g': 354,
        'protein_per_100g': 3.3,
        'carbs_per_100g': 15.2,
        'fats_per_100g': 33.5,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
]

# Protein Sources
PROTEINS = [
    {
        'name': 'eggs',
        'name_hindi': 'अंडे',
        'category': 'protein',
        'calories_per_100g': 155,
        'protein_per_100g': 13.0,
        'carbs_per_100g': 1.1,
        'fats_per_100g': 11.0,
        'typical_unit': 'piece',
        'is_allergen': True,
        'allergen_type': 'eggs'
    },
    {
        'name': 'paneer',
        'name_hindi': 'पनीर',
        'category': 'protein',
        'calories_per_100g': 265,
        'protein_per_100g': 18.3,
        'carbs_per_100g': 1.2,
        'fats_per_100g': 20.8,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'dairy'
    },
    {
        'name': 'chicken_breast',
        'name_hindi': 'चिकन ब्रेस्ट',
        'category': 'protein',
        'calories_per_100g': 165,
        'protein_per_100g': 31.0,
        'carbs_per_100g': 0.0,
        'fats_per_100g': 3.6,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'fish',
        'name_hindi': 'मछली',
        'category': 'protein',
        'calories_per_100g': 206,
        'protein_per_100g': 22.0,
        'carbs_per_100g': 0.0,
        'fats_per_100g': 12.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'fish'
    },
    {
        'name': 'tofu',
        'name_hindi': 'टोफू',
        'category': 'protein',
        'calories_per_100g': 76,
        'protein_per_100g': 8.0,
        'carbs_per_100g': 1.9,
        'fats_per_100g': 4.8,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'soy'
    },
]

# Grains
GRAINS = [
    {
        'name': 'rice',
        'name_hindi': 'चावल',
        'category': 'grain',
        'calories_per_100g': 130,
        'protein_per_100g': 2.7,
        'carbs_per_100g': 28.2,
        'fats_per_100g': 0.3,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'whole_wheat_flour',
        'name_hindi': 'आटा',
        'category': 'grain',
        'calories_per_100g': 340,
        'protein_per_100g': 13.2,
        'carbs_per_100g': 72.0,
        'fats_per_100g': 1.7,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'wheat'
    },
    {
        'name': 'rolled_oats',
        'name_hindi': 'ओट्स',
        'category': 'grain',
        'calories_per_100g': 389,
        'protein_per_100g': 16.9,
        'carbs_per_100g': 66.3,
        'fats_per_100g': 6.9,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'multigrain_bread',
        'name_hindi': 'मल्टीग्रेन ब्रेड',
        'category': 'grain',
        'calories_per_100g': 265,
        'protein_per_100g': 13.4,
        'carbs_per_100g': 43.3,
        'fats_per_100g': 4.2,
        'typical_unit': 'slice',
        'is_allergen': True,
        'allergen_type': 'wheat'
    },
    {
        'name': 'whole_wheat_bread',
        'name_hindi': 'गेहूं की ब्रेड',
        'category': 'grain',
        'calories_per_100g': 247,
        'protein_per_100g': 13.0,
        'carbs_per_100g': 41.0,
        'fats_per_100g': 3.4,
        'typical_unit': 'slice',
        'is_allergen': True,
        'allergen_type': 'wheat'
    },
    {
        'name': 'bread',
        'name_hindi': 'ब्रेड',
        'category': 'grain',
        'calories_per_100g': 265,
        'protein_per_100g': 9.0,
        'carbs_per_100g': 49.0,
        'fats_per_100g': 3.2,
        'typical_unit': 'slice',
        'is_allergen': True,
        'allergen_type': 'wheat'
    },
    {
        'name': 'poha',
        'name_hindi': 'पोहा',
        'category': 'grain',
        'calories_per_100g': 350,
        'protein_per_100g': 6.6,
        'carbs_per_100g': 77.3,
        'fats_per_100g': 0.5,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'semolina',
        'name_hindi': 'सूजी',
        'category': 'grain',
        'calories_per_100g': 360,
        'protein_per_100g': 12.7,
        'carbs_per_100g': 72.8,
        'fats_per_100g': 1.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'wheat'
    },
    {
        'name': 'vermicelli',
        'name_hindi': 'सेवई',
        'category': 'grain',
        'calories_per_100g': 357,
        'protein_per_100g': 11.0,
        'carbs_per_100g': 75.0,
        'fats_per_100g': 1.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'wheat'
    },
    {
        'name': 'quinoa',
        'name_hindi': 'क्विनोआ',
        'category': 'grain',
        'calories_per_100g': 120,
        'protein_per_100g': 4.4,
        'carbs_per_100g': 21.3,
        'fats_per_100g': 1.9,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'rice_flour',
        'name_hindi': 'चावल का आटा',
        'category': 'grain',
        'calories_per_100g': 366,
        'protein_per_100g': 6.0,
        'carbs_per_100g': 80.0,
        'fats_per_100g': 1.4,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'ragi_flour',
        'name_hindi': 'रागी आटा',
        'category': 'grain',
        'calories_per_100g': 328,
        'protein_per_100g': 7.3,
        'carbs_per_100g': 72.0,
        'fats_per_100g': 1.3,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
]

# Lentils and Legumes
LENTILS = [
    {
        'name': 'moong_dal',
        'name_hindi': 'मूंग दाल',
        'category': 'protein',
        'calories_per_100g': 347,
        'protein_per_100g': 24.0,
        'carbs_per_100g': 59.0,
        'fats_per_100g': 1.2,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'toor_dal',
        'name_hindi': 'तूर दाल',
        'category': 'protein',
        'calories_per_100g': 343,
        'protein_per_100g': 22.0,
        'carbs_per_100g': 62.0,
        'fats_per_100g': 1.5,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'urad_dal',
        'name_hindi': 'उड़द दाल',
        'category': 'protein',
        'calories_per_100g': 341,
        'protein_per_100g': 25.0,
        'carbs_per_100g': 59.0,
        'fats_per_100g': 1.6,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'chickpeas',
        'name_hindi': 'चना',
        'category': 'protein',
        'calories_per_100g': 364,
        'protein_per_100g': 19.0,
        'carbs_per_100g': 61.0,
        'fats_per_100g': 6.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'besan',
        'name_hindi': 'बेसन',
        'category': 'grain',
        'calories_per_100g': 387,
        'protein_per_100g': 22.0,
        'carbs_per_100g': 58.0,
        'fats_per_100g': 6.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
]

# Dairy Products
DAIRY = [
    {
        'name': 'milk',
        'name_hindi': 'दूध',
        'category': 'dairy',
        'calories_per_100g': 42,
        'protein_per_100g': 3.4,
        'carbs_per_100g': 5.0,
        'fats_per_100g': 1.0,
        'typical_unit': 'ml',
        'is_allergen': True,
        'allergen_type': 'dairy'
    },
    {
        'name': 'curd',
        'name_hindi': 'दही',
        'category': 'dairy',
        'calories_per_100g': 60,
        'protein_per_100g': 3.5,
        'carbs_per_100g': 4.7,
        'fats_per_100g': 3.3,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'dairy'
    },
    {
        'name': 'greek_yogurt',
        'name_hindi': 'ग्रीक दही',
        'category': 'dairy',
        'calories_per_100g': 59,
        'protein_per_100g': 10.0,
        'carbs_per_100g': 3.6,
        'fats_per_100g': 0.4,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'dairy'
    },
    {
        'name': 'butter',
        'name_hindi': 'मक्खन',
        'category': 'dairy',
        'calories_per_100g': 717,
        'protein_per_100g': 0.9,
        'carbs_per_100g': 0.1,
        'fats_per_100g': 81.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'dairy'
    },
    {
        'name': 'ghee',
        'name_hindi': 'घी',
        'category': 'dairy',
        'calories_per_100g': 900,
        'protein_per_100g': 0.0,
        'carbs_per_100g': 0.0,
        'fats_per_100g': 100.0,
        'typical_unit': 'ml',
        'is_allergen': True,
        'allergen_type': 'dairy'
    },
    {
        'name': 'cheese',
        'name_hindi': 'चीज़',
        'category': 'dairy',
        'calories_per_100g': 402,
        'protein_per_100g': 25.0,
        'carbs_per_100g': 1.3,
        'fats_per_100g': 33.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'dairy'
    },
    {
        'name': 'coconut_milk',
        'name_hindi': 'नारियल का दूध',
        'category': 'dairy',
        'calories_per_100g': 230,
        'protein_per_100g': 2.3,
        'carbs_per_100g': 6.0,
        'fats_per_100g': 24.0,
        'typical_unit': 'ml',
        'is_allergen': False,
        'allergen_type': None
    },
]

# Nuts and Seeds
NUTS_SEEDS = [
    {
        'name': 'almonds',
        'name_hindi': 'बादाम',
        'category': 'protein',
        'calories_per_100g': 579,
        'protein_per_100g': 21.0,
        'carbs_per_100g': 22.0,
        'fats_per_100g': 50.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'tree_nuts'
    },
    {
        'name': 'cashews',
        'name_hindi': 'काजू',
        'category': 'protein',
        'calories_per_100g': 553,
        'protein_per_100g': 18.0,
        'carbs_per_100g': 30.0,
        'fats_per_100g': 44.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'tree_nuts'
    },
    {
        'name': 'peanuts',
        'name_hindi': 'मूंगफली',
        'category': 'protein',
        'calories_per_100g': 567,
        'protein_per_100g': 26.0,
        'carbs_per_100g': 16.0,
        'fats_per_100g': 49.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'peanuts'
    },
    {
        'name': 'chia_seeds',
        'name_hindi': 'चिया बीज',
        'category': 'grain',
        'calories_per_100g': 486,
        'protein_per_100g': 16.5,
        'carbs_per_100g': 42.0,
        'fats_per_100g': 31.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'granola',
        'name_hindi': 'ग्रेनोला',
        'category': 'grain',
        'calories_per_100g': 471,
        'protein_per_100g': 10.0,
        'carbs_per_100g': 64.0,
        'fats_per_100g': 20.0,
        'typical_unit': 'g',
        'is_allergen': True,
        'allergen_type': 'tree_nuts'
    },
]

# Spices and Seasonings
SPICES = [
    {
        'name': 'salt',
        'name_hindi': 'नमक',
        'category': 'spice',
        'calories_per_100g': 0,
        'protein_per_100g': 0.0,
        'carbs_per_100g': 0.0,
        'fats_per_100g': 0.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'black_pepper',
        'name_hindi': 'काली मिर्च',
        'category': 'spice',
        'calories_per_100g': 251,
        'protein_per_100g': 10.4,
        'carbs_per_100g': 64.0,
        'fats_per_100g': 3.3,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'turmeric',
        'name_hindi': 'हल्दी',
        'category': 'spice',
        'calories_per_100g': 312,
        'protein_per_100g': 9.7,
        'carbs_per_100g': 67.0,
        'fats_per_100g': 3.3,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'cumin_seeds',
        'name_hindi': 'जीरा',
        'category': 'spice',
        'calories_per_100g': 375,
        'protein_per_100g': 17.8,
        'carbs_per_100g': 44.0,
        'fats_per_100g': 22.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'cumin_powder',
        'name_hindi': 'जीरा पाउडर',
        'category': 'spice',
        'calories_per_100g': 375,
        'protein_per_100g': 17.8,
        'carbs_per_100g': 44.0,
        'fats_per_100g': 22.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'mustard_seeds',
        'name_hindi': 'सरसों',
        'category': 'spice',
        'calories_per_100g': 508,
        'protein_per_100g': 26.0,
        'carbs_per_100g': 28.0,
        'fats_per_100g': 36.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'curry_leaves',
        'name_hindi': 'करी पत्ता',
        'category': 'spice',
        'calories_per_100g': 108,
        'protein_per_100g': 6.1,
        'carbs_per_100g': 18.7,
        'fats_per_100g': 1.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'red_chili_powder',
        'name_hindi': 'लाल मिर्च पाउडर',
        'category': 'spice',
        'calories_per_100g': 282,
        'protein_per_100g': 12.0,
        'carbs_per_100g': 50.0,
        'fats_per_100g': 17.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'cinnamon',
        'name_hindi': 'दालचीनी',
        'category': 'spice',
        'calories_per_100g': 247,
        'protein_per_100g': 4.0,
        'carbs_per_100g': 81.0,
        'fats_per_100g': 1.2,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'ginger',
        'name_hindi': 'अदरक',
        'category': 'spice',
        'calories_per_100g': 80,
        'protein_per_100g': 1.8,
        'carbs_per_100g': 18.0,
        'fats_per_100g': 0.8,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'garlic',
        'name_hindi': 'लहसुन',
        'category': 'spice',
        'calories_per_100g': 149,
        'protein_per_100g': 6.4,
        'carbs_per_100g': 33.0,
        'fats_per_100g': 0.5,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'sambar_powder',
        'name_hindi': 'सांभर पाउडर',
        'category': 'spice',
        'calories_per_100g': 325,
        'protein_per_100g': 12.0,
        'carbs_per_100g': 55.0,
        'fats_per_100g': 10.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
]

# Oils and Fats
OILS = [
    {
        'name': 'oil',
        'name_hindi': 'तेल',
        'category': 'oil',
        'calories_per_100g': 884,
        'protein_per_100g': 0.0,
        'carbs_per_100g': 0.0,
        'fats_per_100g': 100.0,
        'typical_unit': 'ml',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'olive_oil',
        'name_hindi': 'जैतून का तेल',
        'category': 'oil',
        'calories_per_100g': 884,
        'protein_per_100g': 0.0,
        'carbs_per_100g': 0.0,
        'fats_per_100g': 100.0,
        'typical_unit': 'ml',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'coconut_oil',
        'name_hindi': 'नारियल तेल',
        'category': 'oil',
        'calories_per_100g': 862,
        'protein_per_100g': 0.0,
        'carbs_per_100g': 0.0,
        'fats_per_100g': 100.0,
        'typical_unit': 'ml',
        'is_allergen': False,
        'allergen_type': None
    },
]

# Other Ingredients
OTHER = [
    {
        'name': 'honey',
        'name_hindi': 'शहद',
        'category': 'other',
        'calories_per_100g': 304,
        'protein_per_100g': 0.3,
        'carbs_per_100g': 82.0,
        'fats_per_100g': 0.0,
        'typical_unit': 'ml',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'lemon_juice',
        'name_hindi': 'नींबू का रस',
        'category': 'other',
        'calories_per_100g': 22,
        'protein_per_100g': 0.4,
        'carbs_per_100g': 6.9,
        'fats_per_100g': 0.2,
        'typical_unit': 'ml',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'tamarind',
        'name_hindi': 'इमली',
        'category': 'other',
        'calories_per_100g': 239,
        'protein_per_100g': 2.8,
        'carbs_per_100g': 62.0,
        'fats_per_100g': 0.6,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'idli_batter',
        'name_hindi': 'इडली बैटर',
        'category': 'other',
        'calories_per_100g': 90,
        'protein_per_100g': 3.0,
        'carbs_per_100g': 18.0,
        'fats_per_100g': 0.5,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'dosa_batter',
        'name_hindi': 'डोसा बैटर',
        'category': 'other',
        'calories_per_100g': 95,
        'protein_per_100g': 3.2,
        'carbs_per_100g': 19.0,
        'fats_per_100g': 0.6,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
    {
        'name': 'sabudana',
        'name_hindi': 'साबूदाना',
        'category': 'grain',
        'calories_per_100g': 358,
        'protein_per_100g': 0.2,
        'carbs_per_100g': 88.0,
        'fats_per_100g': 0.0,
        'typical_unit': 'g',
        'is_allergen': False,
        'allergen_type': None
    },
]

# Combine all ingredients
INGREDIENTS = (
    VEGETABLES +
    FRUITS +
    PROTEINS +
    GRAINS +
    LENTILS +
    DAIRY +
    NUTS_SEEDS +
    SPICES +
    OILS +
    OTHER
)

# Additional Vegetables
ADDITIONAL_VEGETABLES = [
    {'name': 'eggplant', 'name_hindi': 'बैंगन', 'category': 'vegetable', 'calories_per_100g': 25, 'protein_per_100g': 1.0, 'carbs_per_100g': 6.0, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'okra', 'name_hindi': 'भिंडी', 'category': 'vegetable', 'calories_per_100g': 33, 'protein_per_100g': 1.9, 'carbs_per_100g': 7.5, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'bitter_gourd', 'name_hindi': 'करेला', 'category': 'vegetable', 'calories_per_100g': 17, 'protein_per_100g': 1.0, 'carbs_per_100g': 3.7, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'bottle_gourd', 'name_hindi': 'लौकी', 'category': 'vegetable', 'calories_per_100g': 14, 'protein_per_100g': 0.6, 'carbs_per_100g': 3.4, 'fats_per_100g': 0.0, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'ridge_gourd', 'name_hindi': 'तोरी', 'category': 'vegetable', 'calories_per_100g': 20, 'protein_per_100g': 1.2, 'carbs_per_100g': 4.4, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'pumpkin', 'name_hindi': 'कद्दू', 'category': 'vegetable', 'calories_per_100g': 26, 'protein_per_100g': 1.0, 'carbs_per_100g': 6.5, 'fats_per_100g': 0.1, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'radish', 'name_hindi': 'मूली', 'category': 'vegetable', 'calories_per_100g': 16, 'protein_per_100g': 0.7, 'carbs_per_100g': 3.4, 'fats_per_100g': 0.1, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'beetroot', 'name_hindi': 'चुकंदर', 'category': 'vegetable', 'calories_per_100g': 43, 'protein_per_100g': 1.6, 'carbs_per_100g': 9.6, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'sweet_potato', 'name_hindi': 'शकरकंद', 'category': 'vegetable', 'calories_per_100g': 86, 'protein_per_100g': 1.6, 'carbs_per_100g': 20.1, 'fats_per_100g': 0.1, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'mushroom', 'name_hindi': 'मशरूम', 'category': 'vegetable', 'calories_per_100g': 22, 'protein_per_100g': 3.1, 'carbs_per_100g': 3.3, 'fats_per_100g': 0.3, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'corn', 'name_hindi': 'मक्का', 'category': 'vegetable', 'calories_per_100g': 86, 'protein_per_100g': 3.3, 'carbs_per_100g': 19.0, 'fats_per_100g': 1.4, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'french_beans', 'name_hindi': 'फ्रेंच बीन्स', 'category': 'vegetable', 'calories_per_100g': 31, 'protein_per_100g': 1.8, 'carbs_per_100g': 7.0, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'mint_leaves', 'name_hindi': 'पुदीना', 'category': 'vegetable', 'calories_per_100g': 44, 'protein_per_100g': 3.8, 'carbs_per_100g': 8.4, 'fats_per_100g': 0.7, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'lettuce', 'name_hindi': 'सलाद पत्ता', 'category': 'vegetable', 'calories_per_100g': 15, 'protein_per_100g': 1.4, 'carbs_per_100g': 2.9, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
]

# Additional Fruits
ADDITIONAL_FRUITS = [
    {'name': 'mango', 'name_hindi': 'आम', 'category': 'fruit', 'calories_per_100g': 60, 'protein_per_100g': 0.8, 'carbs_per_100g': 15.0, 'fats_per_100g': 0.4, 'typical_unit': 'piece', 'is_allergen': False, 'allergen_type': None},
    {'name': 'papaya', 'name_hindi': 'पपीता', 'category': 'fruit', 'calories_per_100g': 43, 'protein_per_100g': 0.5, 'carbs_per_100g': 11.0, 'fats_per_100g': 0.3, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'orange', 'name_hindi': 'संतरा', 'category': 'fruit', 'calories_per_100g': 47, 'protein_per_100g': 0.9, 'carbs_per_100g': 11.8, 'fats_per_100g': 0.1, 'typical_unit': 'piece', 'is_allergen': False, 'allergen_type': None},
    {'name': 'pomegranate', 'name_hindi': 'अनार', 'category': 'fruit', 'calories_per_100g': 83, 'protein_per_100g': 1.7, 'carbs_per_100g': 18.7, 'fats_per_100g': 1.2, 'typical_unit': 'piece', 'is_allergen': False, 'allergen_type': None},
    {'name': 'watermelon', 'name_hindi': 'तरबूज', 'category': 'fruit', 'calories_per_100g': 30, 'protein_per_100g': 0.6, 'carbs_per_100g': 7.6, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'grapes', 'name_hindi': 'अंगूर', 'category': 'fruit', 'calories_per_100g': 69, 'protein_per_100g': 0.7, 'carbs_per_100g': 18.1, 'fats_per_100g': 0.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'guava', 'name_hindi': 'अमरूद', 'category': 'fruit', 'calories_per_100g': 68, 'protein_per_100g': 2.6, 'carbs_per_100g': 14.3, 'fats_per_100g': 1.0, 'typical_unit': 'piece', 'is_allergen': False, 'allergen_type': None},
]

# Additional Proteins
ADDITIONAL_PROTEINS = [
    {'name': 'mutton', 'name_hindi': 'मटन', 'category': 'protein', 'calories_per_100g': 294, 'protein_per_100g': 25.0, 'carbs_per_100g': 0.0, 'fats_per_100g': 21.0, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'prawns', 'name_hindi': 'झींगा', 'category': 'protein', 'calories_per_100g': 99, 'protein_per_100g': 24.0, 'carbs_per_100g': 0.2, 'fats_per_100g': 0.3, 'typical_unit': 'g', 'is_allergen': True, 'allergen_type': 'shellfish'},
    {'name': 'salmon', 'name_hindi': 'सैल्मन', 'category': 'protein', 'calories_per_100g': 208, 'protein_per_100g': 20.0, 'carbs_per_100g': 0.0, 'fats_per_100g': 13.0, 'typical_unit': 'g', 'is_allergen': True, 'allergen_type': 'fish'},
    {'name': 'soya_chunks', 'name_hindi': 'सोया चंक्स', 'category': 'protein', 'calories_per_100g': 345, 'protein_per_100g': 52.0, 'carbs_per_100g': 33.0, 'fats_per_100g': 0.5, 'typical_unit': 'g', 'is_allergen': True, 'allergen_type': 'soy'},
    {'name': 'kidney_beans', 'name_hindi': 'राजमा', 'category': 'protein', 'calories_per_100g': 333, 'protein_per_100g': 24.0, 'carbs_per_100g': 60.0, 'fats_per_100g': 0.8, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'black_gram', 'name_hindi': 'काला चना', 'category': 'protein', 'calories_per_100g': 378, 'protein_per_100g': 25.0, 'carbs_per_100g': 63.0, 'fats_per_100g': 5.0, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
]

# Additional Grains and Batters
ADDITIONAL_GRAINS = [
    {'name': 'brown_rice', 'name_hindi': 'ब्राउन राइस', 'category': 'grain', 'calories_per_100g': 111, 'protein_per_100g': 2.6, 'carbs_per_100g': 23.0, 'fats_per_100g': 0.9, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'basmati_rice', 'name_hindi': 'बासमती चावल', 'category': 'grain', 'calories_per_100g': 121, 'protein_per_100g': 3.5, 'carbs_per_100g': 25.0, 'fats_per_100g': 0.4, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'barley', 'name_hindi': 'जौ', 'category': 'grain', 'calories_per_100g': 354, 'protein_per_100g': 12.5, 'carbs_per_100g': 73.5, 'fats_per_100g': 2.3, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
    {'name': 'millet', 'name_hindi': 'बाजरा', 'category': 'grain', 'calories_per_100g': 378, 'protein_per_100g': 11.0, 'carbs_per_100g': 73.0, 'fats_per_100g': 4.2, 'typical_unit': 'g', 'is_allergen': False, 'allergen_type': None},
]

# Update the combined list
INGREDIENTS = (
    VEGETABLES +
    FRUITS +
    PROTEINS +
    GRAINS +
    LENTILS +
    DAIRY +
    NUTS_SEEDS +
    SPICES +
    OILS +
    OTHER +
    ADDITIONAL_VEGETABLES +
    ADDITIONAL_FRUITS +
    ADDITIONAL_PROTEINS +
    ADDITIONAL_GRAINS
)
