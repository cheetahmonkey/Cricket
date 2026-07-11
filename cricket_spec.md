# Daily Used Subaru Crosstrek Search Agent Spec

## 1. Purpose

Build a daily search agent that finds used Subaru Crosstrek listings suitable for Mom’s replacement car search.

The agent should search for used Subaru Crosstreks that match Mom’s required safety-feature set, score each opportunity, and produce a ranked daily report.

The agent should prioritize practical, low-risk, local purchasing opportunities over theoretical best prices.

## 2. Buyer Profile

Buyer: Mom
Location: Edmonds, WA 98026
Preferred dealer: Carter Subaru, especially Carter Subaru Shoreline
Use case: local town driving, errands, gardening, easy parking, safer replacement for 1994 Subaru Legacy
Preferred model: Subaru Crosstrek
Forester rejected as too large
Condition: used
Primary priority: correct size + safety features + low-hassle purchase

## 3. Required Vehicle

### Required model

Subaru Crosstrek only.

Exclude:

* Forester
* Outback
* Impreza hatchback
* Solterra
* Legacy
* Ascent
* Any non-Subaru models

### Preferred years

Primary target:

* 2021–2024 Subaru Crosstrek Limited

Acceptable with caution:

* 2020 Crosstrek Limited, only if low mileage, clean history, and clearly good value
* 2024 Crosstrek Limited, if not overpriced

Do not prioritize:

* 2019 or older unless explicitly requested later
* 2025+ unless used pricing becomes attractive and it fits the criteria

### Required trim

Primary target:

* Limited

Allowed if safety features can be verified:

* Premium, Sport, or other trims only if the listing or window sticker confirms the full required rear-safety feature set.

Default assumption:

* Limited is the safest trim target because it is most likely to include the required features.

## 4. Required Feature Set

Every candidate must be evaluated for the following:

1. Rear-view camera
2. Blind Spot Detection, abbreviated BSD
3. Rear Cross-Traffic Alert, abbreviated RCTA
4. Reverse Automatic Braking, abbreviated RAB

The agent must treat RAB as a separately confirmed feature.

Important: Do not assume RAB is present just because the listing says:

* backup camera
* rear camera
* blind spot monitor
* rear cross traffic alert
* EyeSight
* driver assistance package
* safety package

A vehicle can have a rear camera and RCTA without RAB.

## 5. Hard Filters

A listing should only be included in the main ranked list if it satisfies these hard filters:

| Filter           | Requirement                                                                                                 |
| ---------------- | ----------------------------------------------------------------------------------------------------------- |
| Make             | Subaru                                                                                                      |
| Model            | Crosstrek                                                                                                   |
| Condition        | Used or CPO                                                                                                 |
| Year             | 2020 or newer                                                                                               |
| Mileage          | Under 45,000 miles                                                                                          |
| Title            | Clean title preferred; exclude salvage/rebuilt/lemon/buyback unless explicitly flagged in rejected listings |
| Location         | Washington preferred; Oregon acceptable only if value is strong                                             |
| Transmission     | Automatic/CVT                                                                                               |
| Drivetrain       | AWD                                                                                                         |
| Must-have safety | Rear camera + BSD + RCTA + RAB, confirmed or likely enough to verify                                        |

## 6. Geography

Use Mom’s address as the reference point:

Edmonds, WA 98026

### Preferred search radius

Primary:

* 0–50 miles from Edmonds

Secondary:

* 50–100 miles if price/value is strong

Tertiary:

* 100–200 miles, including Portland/Vancouver/Salem, only if the listing is meaningfully better than local options.

### Dealer priority

Highest preference:

1. Carter Subaru Shoreline
2. Carter Subaru Ballard / Carter Subaru family if applicable
3. Subaru dealers near Edmonds: Marysville, Puyallup, Tacoma, Bellevue, Renton, Everett, Seattle
4. Reputable non-Subaru franchised dealers
5. Large used-car retailers
6. Private sellers / Craigslist / Facebook Marketplace, only if data is complete and risk is manageable

## 7. Search Sources

The agent should support multiple sources, but the initial implementation should search **Tier 1 only**.

### Tier 1 sources — initial search scope

Start with these sources only:

* Carter Subaru Shoreline used inventory
* Carter Subaru Ballard / Carter Subaru group inventory, if separate
* Subaru certified pre-owned inventory
* Dealer websites for local Subaru dealerships

### Tier 2 sources — later expansion

Do not include these in the initial search implementation. Add them only after Tier 1 is working reliably.

* Autotrader
* Cars.com
* CarGurus
* CARFAX used cars

### Tier 3 sources — optional future expansion

These are lower priority and should not be part of the initial build.

* Craigslist Seattle
* Facebook Marketplace, if accessible
* Edmunds
* TrueCar
* AutoNation
* CarMax
* Enterprise Car Sales, if relevant

### Important source-handling rule

Respect each site’s terms of service and robots rules. Prefer official APIs, RSS/search URLs, email alerts, or manual export where available. Do not build fragile or prohibited scraping if a source disallows it.

## 8. Search Queries

For Tier 1 only, use combinations of these:

* `Subaru Crosstrek Limited 2021 2022 2023 2024 under 45000 miles Edmonds WA`
* `used Subaru Crosstrek Limited Reverse Automatic Braking`
* `used Subaru Crosstrek Limited blind spot rear cross traffic`
* `Subaru Crosstrek Limited CPO Washington`
* `site:cartersubarushoreline.com Crosstrek Limited used`
* `site:cartersubaru.com Crosstrek Limited used`
* `site:subaru.com certified pre owned Crosstrek Limited Washington`
* `Subaru certified pre-owned Crosstrek Limited Washington`

Save these Tier 2 queries for future use, but do not run them in Phase 1:

* `site:autotrader.com Subaru Crosstrek Limited Seattle`
* `site:cars.com Subaru Crosstrek Limited Seattle`
* `site:cargurus.com Subaru Crosstrek Limited Seattle`
* `site:carfax.com Subaru Crosstrek Limited Seattle WA`

## 9. Data Model

For every listing, collect as many of these fields as available:

| Field                     | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| listing_id                | Source-specific listing ID if available                      |
| source                    | Site or dealer name                                          |
| source_url                | Listing URL                                                  |
| dealer_name               | Dealer or seller                                             |
| dealer_type               | Subaru dealer / franchise dealer / used-car dealer / private |
| location                  | City, state                                                  |
| distance_miles            | Estimated distance from Edmonds, WA                          |
| year                      | Model year                                                   |
| make                      | Subaru                                                       |
| model                     | Crosstrek                                                    |
| trim                      | Limited, Sport, Premium, etc.                                |
| price                     | Advertised price                                             |
| mileage                   | Odometer miles                                               |
| exterior_color            | If available                                                 |
| interior_color            | If available                                                 |
| color_score               | highest / med_high / med / low                               |
| drivetrain                | AWD                                                          |
| transmission              | CVT/automatic                                                |
| VIN                       | VIN if available                                             |
| stock_number              | Dealer stock number if available                             |
| CPO                       | True/false/unknown                                           |
| accident_history          | none / accident reported / unknown                           |
| owners                    | Number of previous owners if available                       |
| title_status              | clean / salvage / rebuilt / lemon / unknown                  |
| service_records           | Count or summary if available                                |
| rear_camera               | yes/no/unknown                                               |
| blind_spot_detection      | yes/no/unknown                                               |
| rear_cross_traffic_alert  | yes/no/unknown                                               |
| reverse_automatic_braking | yes/no/unknown                                               |
| feature_confidence        | confirmed / likely / unknown / contradicted                  |
| listing_age_days          | Days since first seen                                        |
| first_seen_date           | Date first captured                                          |
| last_seen_date            | Date last observed                                           |
| price_change              | Difference from prior observed price                         |
| notes                     | Human-readable notes                                         |
| reject_reason             | If excluded                                                  |

## 10. Feature Verification Logic

The agent should classify feature confidence as follows:

### Confirmed

Use “confirmed” only when one or more of the following is true:

* Listing explicitly says Reverse Automatic Braking
* Window sticker confirms Reverse Automatic Braking
* Dealer description explicitly lists RAB
* VIN decoder or Subaru build sheet confirms RAB
* A trusted dealer confirms in text/email

### Likely

Use “likely” when:

* Vehicle is a 2021–2024 Crosstrek Limited
* Listing shows BSD/RCTA
* Listing has a safety/package description consistent with RAB
* No evidence contradicts RAB

Likely vehicles should remain in the report but be marked “verify RAB.”

### Unknown

Use “unknown” when:

* Listing lacks enough detail
* Trim is not Limited
* Safety features are incomplete or vague

Unknown vehicles may appear in a secondary “Needs Verification” section, not the main top-ranked list.

### Contradicted

Use “contradicted” when:

* Listing says it lacks the feature
* Trim/package is known not to include the feature
* Photos show missing controls/features where relevant

Contradicted vehicles should be excluded from the main list.

## 11. Scoring System

Score each candidate out of 100 points.

### Score categories

| Category                             | Points |
| ------------------------------------ | -----: |
| Required feature confidence          |     25 |
| Price/value                          |     20 |
| Mileage                              |     15 |
| Year/model desirability              |     10 |
| Seller quality / purchase confidence |     10 |
| Distance/convenience                 |     10 |
| Vehicle history                      |      5 |
| Mom-fit extras                       |      5 |
| Total                                |    100 |

### Color scoring

Color is scored as part of **Mom-fit extras** and should also be captured separately as `color_score`.

| Color tier | Colors              | Treatment                                                                      |
| ---------- | ------------------- | ------------------------------------------------------------------------------ |
| Highest    | Blue, teal          | Best colors; add color bonus                                                   |
| Med-High   | Burgundy, green     | Good colors; add partial color bonus                                           |
| Med        | White               | Acceptable / neutral                                                           |
| Low        | Black, silver, gray | Lower priority; no color bonus unless the total listing is otherwise excellent |

The scoring system should not reject a listing based on color alone. Color should influence ranking only after safety, price, mileage, seller quality, and vehicle history.

## 12. Detailed Scoring Rules

### A. Required feature confidence: 25 points

| Condition                                                        |        Points |
| ---------------------------------------------------------------- | ------------: |
| RAB + BSD + RCTA + rear camera confirmed                         |            25 |
| RAB likely; BSD/RCTA/rear camera confirmed                       |            20 |
| Limited trim and likely rear safety package but incomplete proof |            15 |
| BSD/RCTA confirmed but RAB unknown                               |            10 |
| Rear camera only / vague safety claims                           |             3 |
| RAB contradicted or missing                                      | 0 and exclude |

### B. Price/value: 20 points

Compare against estimated fair market value for year/trim/mileage.

| Condition                                         | Points |
| ------------------------------------------------- | -----: |
| Great deal, at least $1,500 below expected market |     20 |
| Good deal, $500–$1,500 below market               |     16 |
| Fair market                                       |     12 |
| Slightly high, $500–$1,500 over market            |      7 |
| Overpriced by more than $1,500                    |      2 |

If market value cannot be estimated, assign 10 and mark `price_confidence = unknown`.

### C. Mileage: 15 points

| Mileage       |        Points |
| ------------- | ------------: |
| Under 15,000  |            15 |
| 15,000–24,999 |            13 |
| 25,000–34,999 |            10 |
| 35,000–44,999 |             7 |
| 45,000+       | 0 and exclude |

### D. Year/model desirability: 10 points

| Year                                | Points |
| ----------------------------------- | -----: |
| 2024 Limited                        |     10 |
| 2023 Limited                        |      9 |
| 2022 Limited                        |      8 |
| 2021 Limited                        |      7 |
| 2020 Limited                        |      5 |
| Non-Limited with confirmed features |      4 |

### E. Seller quality / purchase confidence: 10 points

| Seller                      | Points |
| --------------------------- | -----: |
| Carter Subaru               |     10 |
| Subaru CPO dealer           |      9 |
| Other Subaru dealer         |      8 |
| Reputable franchised dealer |      6 |
| Large used-car retailer     |      5 |
| Independent dealer          |      3 |
| Private seller              |      2 |

### F. Distance/convenience: 10 points

| Distance from Edmonds |               Points |
| --------------------- | -------------------: |
| 0–15 miles            |                   10 |
| 16–30 miles           |                    8 |
| 31–50 miles           |                    6 |
| 51–100 miles          |                    4 |
| 101–200 miles         |                    2 |
| Over 200 miles        | 0 unless exceptional |

### G. Vehicle history: 5 points

| History                                  |        Points |
| ---------------------------------------- | ------------: |
| One owner, no accidents, service records |             5 |
| No accidents, clean title                |             4 |
| Minor accident but well-documented       |             2 |
| Unknown history                          |             1 |
| Salvage/rebuilt/lemon/buyback            | 0 and exclude |

### H. Mom-fit extras: 5 points

Add points for practical comfort, usability, and color preference:

| Extra                                               | Points |
| --------------------------------------------------- | -----: |
| Heated seats                                        |     +1 |
| Power driver seat                                   |     +1 |
| Keyless access/push-button start                    |     +1 |
| Good visibility / light interior / easy entry noted |     +1 |
| Highest color tier: blue or teal                    |     +1 |
| Med-High color tier: burgundy or green              |   +0.5 |
| Med color tier: white                               |  +0.25 |
| Low color tier: black, silver, or gray              |     +0 |

Cap Mom-fit extras at 5.

## 13. Deal Breakers

Exclude or demote hard if any of these appear:

* Salvage/rebuilt/lemon/buyback title
* Open severe recall with no remedy
* Major accident or airbag deployment
* Mileage over 45,000
* Missing RAB if RAB is truly required
* Seller refuses to provide VIN
* Listing price is suspiciously low and details are missing
* Dealer has excessive add-on fees or unclear pricing
* Vehicle is already sold or unavailable
* Manual transmission
* Non-Crosstrek model

## 14. Daily Workflow

The agent should run once per day.

Suggested schedule:

* Morning run: 7:00–8:00 a.m. Pacific
* Optional second run: 5:00 p.m. Pacific if actively shopping

Steps:

1. Search each configured Tier 1 source.
2. Normalize listings into the data model.
3. Deduplicate by VIN first, then by source URL + year + mileage + price.
4. Apply hard filters.
5. Estimate feature confidence.
6. Score each listing.
7. Compare against previous run:

   * new listing
   * removed listing
   * price drop
   * price increase
   * mileage changed
   * feature evidence improved
8. Produce a simplified ranked report.
9. Save historical snapshot.

## 15. Report Output

Generate a daily Markdown report.

Filename format:

`YYYY-MM-DD_crosstrek_search_report.md`

### Simplified report sections

0. **Summary**
   Two to three sentences only. Include whether there are any strong opportunities, whether any Carter/Subaru/CPO listings are notable, and whether action is needed.

1. **Top Opportunities**
   Ranked list of the best candidates.

2. **New / Rejected / Price Drop Listings**
   Compact change log showing new listings, rejected listings with reasons, and price drops.

### Top-opportunity table

Use this format:

| Rank | Score | Year | Trim | Miles | Price | Color | Seller | Distance | Feature confidence | Action |
| ---: | ----: | ---- | ---- | ----: | ----: | ----- | ------ | -------: | ------------------ | ------ |

### Listing detail format

For each top listing:

```markdown
## #1 — 2023 Subaru Crosstrek Limited — 31,200 miles — $26,900

Score: 87/100  
Seller: Carter Subaru Shoreline  
Distance: 5 miles  
Color: Blue — highest color tier  
URL: <listing url>  
VIN: <VIN if available>  
Feature confidence: Likely — verify RAB  

Why it ranks well:
- Limited trim
- Under 45K miles
- Near Mom
- Good price relative to local market
- Seller preference match
- Preferred color

Open questions:
- Confirm Reverse Automatic Braking
- Confirm clean title / accident history
- Ask for out-the-door price
```

## 16. Dealer Contact Script Template

Do not generate dealer scripts automatically in the daily report.

Save this template for future manual use:

```text
Hi, we’re interested in this used Subaru Crosstrek.

Can you confirm whether this specific VIN has all of the following?

1. Rear-view camera
2. Blind Spot Detection
3. Rear Cross-Traffic Alert
4. Reverse Automatic Braking

We are especially trying to confirm Reverse Automatic Braking, not just the backup camera or rear cross-traffic alert.

Can you also send the window sticker, Carfax/Autocheck, and the full out-the-door price including dealer fees?
```

## 17. Storage

Maintain a local data store.

Suggested files:

```text
/data/listings_raw/YYYY-MM-DD.json
/data/listings_normalized/YYYY-MM-DD.json
/data/listings_history.sqlite
/reports/YYYY-MM-DD_crosstrek_search_report.md
/config/search_config.yaml
```

### SQLite tables

Suggested tables:

* listings
* listing_snapshots
* sellers
* feature_evidence
* price_history
* rejected_listings

## 18. Config File

Use a config file so criteria can be adjusted without code changes.

Example:

```yaml
buyer:
  location_zip: "98026"
  preferred_dealers:
    - "Carter Subaru Shoreline"
    - "Carter Subaru Ballard"

vehicle:
  make: "Subaru"
  model: "Crosstrek"
  years_min: 2020
  years_max: 2024
  preferred_years: [2021, 2022, 2023, 2024]
  required_trim_primary: "Limited"
  allowed_trims_if_features_confirmed:
    - "Limited"
    - "Sport"
    - "Premium"
  max_mileage: 45000
  required_drivetrain: "AWD"
  required_transmission: "Automatic/CVT"

features:
  required:
    - "rear camera"
    - "blind spot detection"
    - "rear cross-traffic alert"
    - "reverse automatic braking"
  treat_rab_as_separate_required_feature: true

color_preferences:
  highest:
    - "blue"
    - "teal"
  med_high:
    - "burgundy"
    - "green"
  med:
    - "white"
  low:
    - "black"
    - "silver"
    - "gray"

search:
  initial_scope: "tier1_only"
  primary_radius_miles: 50
  secondary_radius_miles: 100
  tertiary_radius_miles: 200
  include_tier1_sources: true
  include_tier2_sources: false
  include_tier3_sources: false
  include_private_sellers: false
  include_craigslist: false
  include_facebook_marketplace: false
  include_oregon: true

sources:
  tier1:
    - "Carter Subaru Shoreline used inventory"
    - "Carter Subaru Ballard / Carter Subaru group inventory"
    - "Subaru certified pre-owned inventory"
    - "Local Subaru dealership websites"
  tier2:
    - "Autotrader"
    - "Cars.com"
    - "CarGurus"
    - "CARFAX used cars"
  tier3:
    - "Craigslist Seattle"
    - "Facebook Marketplace"
    - "Edmunds"
    - "TrueCar"
    - "AutoNation"
    - "CarMax"
    - "Enterprise Car Sales"

scoring:
  watchlist_threshold: 70
  exclude_below: 50
```

## 19. Implementation Notes for Codex

Build the agent in phases.

### Phase 1: Tier 1 search MVP

Start the search with Tier 1 sources only:

1. Carter Subaru Shoreline used inventory
2. Carter Subaru Ballard / Carter Subaru group inventory, if separate
3. Subaru certified pre-owned inventory
4. Local Subaru dealership websites

Phase 1 must:

* Search Tier 1 sources only.
* Normalize and score listings.
* Generate the simplified Markdown report.
* Save historical snapshots.
* Identify new listings and price changes across runs.

### Phase 2: Tier 2 search integrations

After Tier 1 is reliable, add Tier 2 source adapters one at a time:

1. Autotrader
2. Cars.com
3. CarGurus
4. CARFAX used cars

Each adapter should produce the same normalized listing schema.

### Phase 3: Feature evidence

Add feature-evidence extraction:

* Parse listing text for RAB, Reverse Automatic Braking, BSD, Blind Spot Detection, RCTA, Rear Cross Traffic Alert.
* Parse VIN/window sticker links if available.
* Store evidence text snippets.
* Show feature confidence in report.

### Phase 4: Optional future expansion

Optional later additions:

* Tier 3 sources
* Email alerts
* Slack alerts
* Local desktop notification
* Dealer-script generation

## 20. Quality Bar

The agent should be conservative.

Do not overstate features.
Do not assume RAB unless there is evidence.
Do not rank a cheap car above a safer, cleaner, nearby car unless the value difference is meaningful.
Do not hide uncertainty.
Every recommendation should include “why it ranks well” and “what to verify next.”

## 21. Initial Acceptance Criteria

The first working version is acceptable when it can:

* Search Tier 1 sources only.
* Filter to 2020+ Crosstreks under 45,000 miles.
* Prefer Limited trim.
* Score each listing out of 100.
* Apply color preference scoring.
* Clearly mark RAB as confirmed, likely, unknown, or contradicted.
* Produce a simplified ranked Markdown report.
* Identify new listings and price changes across two runs.
* Save the dealer contact script template for future use without adding it to the daily report.
