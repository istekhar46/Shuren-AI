# Meal Dish Management - Requirements Document

**Feature Name:** meal-dish-management  
**Created:** January 30, 2026  
**Status:** Draft  
**Priority:** High

---

## 1. Executive Summary

This feature extends the existing meal plan system to include **concrete dish recommendations** for each meal slot. Currently, users have abstract meal plans (calories, macros, timing) but no specific guidance on *what to eat*. This enhancement provides:

- Weekly rotating meal templates with specific Indian dishes
- Pre-workout, post-workout, and main meal recommendations
- Flexible meal options (user can choose from alternatives)
- Integration with existing meal schedules and nutritional targets
- Support for dietary preferences (veg/non-veg/vegan)

---

## 2. Problem Statement

### Current State
Users have:
- ✅ Meal timing schedules (when to eat)
- ✅ Nutritional targets (calories, macros)
- ✅ Dietary preferences (veg/non-veg, allergies)
- ❌ **No specific dish recommendations** (what to eat)

### User Pain Points
1. "I know I need 30g protein for breakfast, but what should I cook?"
2. "What ingredients should I buy at the market?"
3. "I'm bored eating the same thing every day"
4. "How do I hit my macro targets with Indian food?"

### Business Impact
- Reduces user drop-off during meal planning phase
- Increases engagement with Diet Planning Agent
- Provides immediate actionable value
- Differentiates from generic calorie trackers

---

## 3. User Stories

### 3.1 As a User Setting Up My Profile
**Story:** As a new user completing onboarding, I want to receive a weekly meal template with specific dishes so that I know exactly what to eat without guessing.

**Acceptance Criteria:**
- [ ] 1.1 After completing onboarding, user receives a 7-day meal template
- [ ] 1.2 Template includes specific dishes for each meal slot
- [ ] 1.3 Dishes respect user's dietary preferences (veg/non-veg/vegan)
- [ ] 1.4 Each dish shows approximate protein, carbs, fats
- [ ] 1.5 Template rotates weekly to prevent boredom

### 3.2 As a User Planning My Day
**Story:** As a user checking my meal schedule, I want to see what dishes are recommended for today so that I can prepare or shop accordingly.

**Acceptance Criteria:**
- [ ] 2.1 GET /meals/today returns meal schedule with dish recommendations
- [ ] 2.2 Each meal slot shows 2-3 dish options to choose from
- [ ] 2.3 Dishes are culturally appropriate (Indian cuisine focus)
- [ ] 2.4 Response includes preparation time and difficulty level
- [ ] 2.5 Dishes align with user's calorie and macro targets

### 3.3 As a User Viewing Next Meal
**Story:** As a user asking "What's my next meal?", I want to see specific dish options so that I can decide what to prepare.

**Acceptance Criteria:**
- [ ] 3.1 GET /meals/next returns next meal with dish recommendations
- [ ] 3.2 Shows 2-3 alternative dishes for flexibility
- [ ] 3.3 Includes ingredient list for selected dish
- [ ] 3.4 Shows nutritional breakdown per dish
- [ ] 3.5 Indicates if dish is pre-workout, post-workout, or regular meal

### 3.4 As a User Shopping for Groceries
**Story:** As a user at the market, I want to see a shopping list for my weekly meal template so that I can buy the right ingredients.

**Acceptance Criteria:**
- [ ] 4.1 GET /meals/shopping-list returns aggregated ingredients
- [ ] 4.2 List is organized by category (vegetables, proteins, grains, etc.)
- [ ] 4.3 Quantities are calculated for 7 days
- [ ] 4.4 Optional items are clearly marked
- [ ] 4.5 List respects dietary preferences and allergies

### 3.5 As a User Wanting Variety
**Story:** As a user bored with my current meal template, I want to request a new template so that I can have variety without losing nutritional balance.

**Acceptance Criteria:**
- [ ] 5.1 POST /meals/template/regenerate creates new template
- [ ] 5.2 New template maintains same calorie and macro targets
- [ ] 5.3 Dishes are different from previous template
- [ ] 5.4 User can specify preferences (e.g., "more chicken dishes")
- [ ] 5.5 Regeneration respects profile lock status

### 3.6 As a User with Dietary Restrictions
**Story:** As a vegetarian user, I want all dish recommendations to be vegetarian so that I never see non-veg options.

**Acceptance Criteria:**
- [ ] 6.1 Dish recommendations filter by dietary_preferences.diet_type
- [ ] 6.2 Allergies and intolerances are excluded from all dishes
- [ ] 6.3 Religious restrictions are respected
- [ ] 6.4 Dislikes are avoided when possible
- [ ] 6.5 System provides alternatives if primary dish conflicts with preferences

---

## 4. Functional Requirements

### 4.1 Meal Template System

**FR-1: Weekly Meal Template Generation**
- System generates a 7-day rotating meal template during onboarding
- Template includes specific dishes for each meal slot
- Dishes are selected based on:
  - User's dietary preferences
  - Nutritional targets (calories, macros)
  - Meal timing (pre-workout, post-workout, regular)
  - Cultural context (Indian cuisine)

**FR-2: Dish Database**
- System maintains a database of dishes with:
  - Dish name (English and regional language)
  - Ingredients with quantities
  - Nutritional information (calories, protein, carbs, fats)
  - Preparation time and difficulty
  - Meal type (breakfast, lunch, dinner, snack)
  - Dietary tags (veg, non-veg, vegan, gluten-free, etc.)
  - Cuisine type (North Indian, South Indian, etc.)

**FR-3: Dish Alternatives**
- Each meal slot provides 2-3 alternative dishes
- Alternatives have similar nutritional profiles (±10% variance)
- User can swap dishes without breaking nutritional balance
- Swaps are persisted to user's meal template

**FR-4: Template Rotation**
- Template rotates weekly (Week 1 → Week 2 → Week 3 → Week 4 → Week 1)
- Each week has different dishes to prevent boredom
- Rotation maintains nutritional consistency
- User can manually regenerate template at any time

### 4.2 Meal Schedule Integration

**FR-5: Dish Assignment to Meal Slots**
- Each meal_schedule entry is linked to recommended dishes
- Dishes are assigned based on meal timing:
  - Pre-workout: Fast-digesting carbs, light protein
  - Post-workout: High protein, moderate carbs
  - Breakfast: Balanced macros, higher calories
  - Snacks: Lower calories, protein-focused
  - Lunch/Dinner: Complete meals with vegetables

**FR-6: Today's Meals with Dishes**
- GET /meals/today returns meal schedule with dish recommendations
- Each meal shows:
  - Scheduled time
  - Meal name (e.g., "Breakfast", "Pre-workout")
  - Primary recommended dish
  - 2 alternative dishes
  - Nutritional breakdown per dish

**FR-7: Next Meal with Dishes**
- GET /meals/next returns next upcoming meal with dishes
- Includes preparation instructions
- Shows ingredient checklist
- Indicates if ingredients are commonly available

### 4.3 Shopping List Generation

**FR-8: Weekly Shopping List**
- GET /meals/shopping-list generates aggregated ingredient list
- Calculates quantities for 7 days
- Organizes by category:
  - Vegetables
  - Proteins (chicken, fish, paneer, eggs, etc.)
  - Grains (rice, oats, bread)
  - Dairy (milk, yogurt, cheese)
  - Pantry (spices, oils, nuts)
- Marks optional items (e.g., "for variety")

**FR-9: Smart Ingredient Aggregation**
- Combines duplicate ingredients across meals
- Converts units consistently (grams, cups, pieces)
- Accounts for typical household inventory (assumes basic spices)
- Provides substitution suggestions

### 4.4 Dietary Preference Enforcement

**FR-10: Dietary Filter**
- All dish recommendations filtered by dietary_preferences.diet_type
- Vegetarian users never see non-veg dishes
- Vegan users see only plant-based options
- Pescatarian users see fish but not meat

**FR-11: Allergy and Intolerance Handling**
- Dishes containing user's allergies are excluded
- Intolerances trigger warnings or alternatives
- System provides safe substitutions
- Critical allergies (peanuts, shellfish) are strictly enforced

**FR-12: Religious and Cultural Restrictions**
- Respects religious_restrictions (no pork, no beef, no alcohol)
- Considers cultural preferences (preferred_cuisines)
- Adapts to regional availability

### 4.5 Template Customization

**FR-13: Manual Template Regeneration**
- POST /meals/template/regenerate creates new template
- Requires profile to be unlocked
- User can specify preferences:
  - "More chicken dishes"
  - "Less spicy food"
  - "Quick prep meals only"
- Creates profile version for audit trail

**FR-14: Dish Swapping**
- PATCH /meals/template/swap allows single dish replacement
- User selects meal slot and new dish
- System validates nutritional compatibility
- Swap is persisted to user's template

**FR-15: Template Locking**
- Template is locked by default (consistent with profile locking)
- User must unlock to make changes
- Lock status inherited from user_profile.is_locked
- Changes create profile version

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **NFR-1:** GET /meals/today response time < 100ms
- **NFR-2:** GET /meals/shopping-list response time < 200ms
- **NFR-3:** Template generation during onboarding < 2 seconds
- **NFR-4:** Dish database queries use proper indexes

### 5.2 Scalability
- **NFR-5:** Support 1M+ users with unique meal templates
- **NFR-6:** Dish database supports 1000+ dishes
- **NFR-7:** Template generation scales horizontally

### 5.3 Data Quality
- **NFR-8:** All dishes have verified nutritional information
- **NFR-9:** Ingredient quantities are realistic and tested
- **NFR-10:** Preparation times are accurate (±5 minutes)

### 5.4 Usability
- **NFR-11:** Dish names are clear and recognizable
- **NFR-12:** Ingredient lists use common terminology
- **NFR-13:** Preparation instructions are concise (< 5 steps)

### 5.5 Maintainability
- **NFR-14:** Dish database is easily updatable by admins
- **NFR-15:** Template generation logic is configurable
- **NFR-16:** Nutritional calculations are auditable

---

## 6. Data Model Requirements

### 6.1 New Tables

**dishes**
- Stores dish definitions with nutritional info
- Fields: name, description, cuisine_type, meal_type, prep_time, difficulty
- Nutritional fields: calories, protein_g, carbs_g, fats_g
- Dietary tags: is_veg, is_vegan, is_gluten_free, etc.
- Relationships: ingredients (many-to-many)

**dish_ingredients**
- Junction table linking dishes to ingredients
- Fields: dish_id, ingredient_id, quantity, unit

**ingredients**
- Master ingredient list
- Fields: name, category, typical_unit, allergen_tags

**meal_templates**
- User's weekly meal template
- Fields: user_id, week_number (1-4), is_active
- Relationships: template_meals (one-to-many)

**template_meals**
- Specific dish assignments for meal slots
- Fields: template_id, meal_schedule_id, dish_id, day_of_week, is_primary
- Relationships: dish, meal_schedule

### 6.2 Modified Tables

**meal_schedules**
- Add relationship to template_meals
- No schema changes required (relationship only)

**dietary_preferences**
- No changes required (already has all needed fields)

---

## 7. API Requirements

### 7.1 New Endpoints

```
GET /api/v1/meals/today
- Returns today's meals with dish recommendations
- Response includes dish details, alternatives, nutritional info

GET /api/v1/meals/next
- Returns next upcoming meal with dishes
- Includes preparation guidance

GET /api/v1/meals/template
- Returns user's current meal template (7 days)
- Shows all dishes for the week

GET /api/v1/meals/template/week/{week_number}
- Returns specific week template (1-4)
- Allows preview of upcoming weeks

GET /api/v1/meals/shopping-list
- Returns aggregated shopping list for current week
- Optional query param: weeks=2 (for 2-week list)

POST /api/v1/meals/template/regenerate
- Generates new meal template
- Request body: preferences (optional)
- Requires unlocked profile

PATCH /api/v1/meals/template/swap
- Swaps a single dish in template
- Request body: meal_slot, new_dish_id
- Requires unlocked profile

GET /api/v1/dishes/search
- Search dish database
- Query params: meal_type, diet_type, max_prep_time
- Returns paginated dish list

GET /api/v1/dishes/{dish_id}
- Get detailed dish information
- Includes ingredients, instructions, nutrition
```

### 7.2 Modified Endpoints

```
GET /api/v1/meals/today
- Enhanced to include dish recommendations
- Backward compatible (dishes are optional in response)

GET /api/v1/meals/next
- Enhanced to include dish recommendations
- Backward compatible
```

---

## 8. Integration Requirements

### 8.1 Onboarding Integration
- **INT-1:** Meal template generation added to onboarding flow
- **INT-2:** Occurs after meal schedule is configured (Step 6)
- **INT-3:** User reviews template before locking profile (Step 10)
- **INT-4:** Template generation uses dietary preferences from Step 4

### 8.2 AI Agent Integration
- **INT-5:** Diet Planning Agent can access dish database
- **INT-6:** Agent can suggest dish swaps based on user queries
- **INT-7:** Agent explains nutritional rationale for dish selections
- **INT-8:** Conversational Assistant can answer "What should I cook?"

### 8.3 Profile Locking Integration
- **INT-9:** Meal template respects profile lock status
- **INT-10:** Template changes create profile versions
- **INT-11:** Template regeneration requires unlock
- **INT-12:** Dish swaps require unlock

---

## 9. Security & Privacy Requirements

### 9.1 Data Access
- **SEC-1:** Users can only access their own meal templates
- **SEC-2:** Dish database is read-only for users
- **SEC-3:** Admin role required to modify dish database

### 9.2 Data Privacy
- **SEC-4:** Meal templates are user-specific (no sharing by default)
- **SEC-5:** Shopping lists don't expose personal health data
- **SEC-6:** Dietary preferences remain private

---

## 10. Testing Requirements

### 10.1 Unit Tests
- Template generation logic
- Nutritional calculation accuracy
- Dietary filter enforcement
- Shopping list aggregation

### 10.2 Integration Tests
- Onboarding flow with template generation
- API endpoints with authentication
- Profile locking behavior
- Database relationships

### 10.3 Property-Based Tests
- **PBT-1:** Template always meets calorie targets (±5%)
- **PBT-2:** Macro percentages always sum to 100 (±1%)
- **PBT-3:** Dietary restrictions are never violated
- **PBT-4:** Shopping list quantities are always positive

---

## 11. Success Metrics

### 11.1 Adoption Metrics
- % of users who view their meal template within 24h of onboarding
- % of users who generate shopping list
- % of users who swap dishes

### 11.2 Engagement Metrics
- Average number of template regenerations per user per month
- Frequency of "What should I cook?" queries to AI agents
- User retention after meal template feature launch

### 11.3 Quality Metrics
- User satisfaction with dish recommendations (survey)
- % of dishes marked as "tried and liked"
- Drop-off rate during onboarding (should decrease)

---

## 12. Out of Scope (Future Enhancements)

### 12.1 Not Included in MVP
- ❌ Recipe instructions (just ingredient lists)
- ❌ Cooking videos or GIFs
- ❌ Meal logging/tracking
- ❌ Calorie counting from photos
- ❌ Restaurant meal recommendations
- ❌ Meal delivery integration
- ❌ Social sharing of meal templates
- ❌ Custom recipe creation by users

### 12.2 Future Considerations
- Multi-week meal planning (beyond 4-week rotation)
- Seasonal dish recommendations
- Regional cuisine preferences (South Indian vs North Indian)
- Budget-based dish filtering
- Meal prep batch cooking suggestions

---

## 13. Dependencies

### 13.1 Technical Dependencies
- Existing meal_plans and meal_schedules tables
- Existing dietary_preferences table
- Profile locking mechanism
- User authentication system

### 13.2 Data Dependencies
- Dish database must be populated before launch
- Nutritional data must be verified
- Ingredient master list must be complete

### 13.3 Team Dependencies
- Nutritionist to verify dish nutritional info
- Chef/cook to validate preparation times
- Content team to write dish descriptions

---

## 14. Risks & Mitigation

### 14.1 Risks

**Risk 1: Inaccurate Nutritional Data**
- Impact: High (users rely on this for fitness goals)
- Probability: Medium
- Mitigation: Professional nutritionist review, multiple data sources

**Risk 2: Cultural Appropriateness**
- Impact: Medium (user dissatisfaction)
- Probability: Low
- Mitigation: Regional testing, user feedback loops

**Risk 3: Ingredient Availability**
- Impact: Medium (users can't find ingredients)
- Probability: Medium
- Mitigation: Focus on common ingredients, provide substitutions

**Risk 4: Template Generation Performance**
- Impact: Low (onboarding slowdown)
- Probability: Low
- Mitigation: Pre-generate templates, async processing

### 14.2 Assumptions
- Users have basic cooking skills
- Users have access to common kitchen equipment
- Users shop at markets with Indian ingredients
- Users are comfortable with Indian cuisine

---

## 15. Acceptance Criteria Summary

This feature is considered complete when:

✅ All user stories have passing acceptance criteria  
✅ All functional requirements are implemented  
✅ All non-functional requirements are met  
✅ All API endpoints are documented and tested  
✅ Dish database has minimum 200 dishes  
✅ Integration with onboarding flow is complete  
✅ Profile locking integration works correctly  
✅ All property-based tests pass  
✅ Performance targets are achieved  
✅ Security requirements are validated  

---

## 16. Glossary

- **Dish**: A specific food item with defined ingredients and nutritional info
- **Meal Template**: A 7-day plan of dish recommendations
- **Meal Slot**: A specific meal time in the user's schedule (e.g., "Breakfast at 8:00 AM")
- **Template Rotation**: Cycling through 4 different weekly templates
- **Dish Swap**: Replacing one dish with another in the template
- **Shopping List**: Aggregated ingredient list for a time period

---

**Document Status:** Ready for Design Phase  
**Next Steps:** Create design.md with technical architecture and implementation details
