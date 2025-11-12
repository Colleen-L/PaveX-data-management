# 📊 POSTER SESSION SCRIPT - Multiple Versions

**Poster Session: Data Management for Smart Cities**
**November 18, 2025 | PMU North & South Ballrooms**
**Time Slots: 9:00-10:00 AM & 1:30-2:30 PM**

---

## 🎯 THE 30-SECOND ELEVATOR PITCH

**Use this when someone walks up to your poster**

> "Hi! Thanks for stopping by. Our project is about managing massive amounts of road condition data for smart cities.
>
> **[Point to Introduction section]** We're working with almost three million images from Fort Wayne, Indiana - images of roads that show potholes, cracks, and other conditions. The challenge is: how do you efficiently store, search, and visualize that much data?
>
> **[Point to Architecture diagram]** Our solution uses Google Cloud BigQuery as a data warehouse, with a Python pipeline that processes the images and a web dashboard for visualization.
>
> **[Point to Results]** We can now query across millions of records in under five seconds, and city planners can use our interactive map to see exactly which roads need attention.
>
> Would you like me to walk you through it in more detail?"

**[Wait for response - if yes, continue to 2-minute version. If no, thank them!]**

---

## 🎯 THE 2-MINUTE OVERVIEW

**Use this for people who want more detail but are still browsing**

> "Great! So let me give you the quick version.
>
> **[Point to Introduction]** The problem: Computer vision for road condition detection generates huge amounts of data. We have two point nine million images covering twenty-six hundred road segments in Fort Wayne. Each image gets classified into categories like 'longitudinal cracks,' 'potholes,' 'manholes,' and so on. We needed a way to manage all this data efficiently.
>
> **[Point to Objective]** Our objectives were: build a scalable data warehouse, create an ETL pipeline to process the raw data, enable fast queries across complex relationships, and create visualizations that non-technical people can use.
>
> **[Point to Methodology]** For technology, we chose Google Cloud BigQuery because it's optimized for analytics. We built a Python ETL pipeline that converts JSON files into a normalized database with seven tables. Then we created a Streamlit dashboard with PowerBI charts and an interactive map.
>
> **[Point to Results chart]** The results: we processed all two point nine million images, organized them into a queryable structure, and achieved query times under five seconds even for complex multi-table joins.
>
> **[Point to Dashboard]** And here's the dashboard - **[show laptop if available]** - you can see the interactive map showing road conditions color-coded by severity. Green is good, orange is moderate issues, red is bad. City planners can click on any segment to see detailed data.
>
> **[Point to Conclusion]** The impact is that cities can now make data-driven decisions about which roads to fix, when to fix them, and how to prioritize their budgets.
>
> Do you have any specific questions about any part?"

**[Wait for questions - use Q&A section below]**

---

## 🎯 THE 5-MINUTE DEEP DIVE

**Use this for judges, faculty, or very interested visitors**

> "Absolutely, I'd be happy to go into more detail.
>
> ### **Background & Motivation** [Point to Introduction]
>
> The project started because we're part of the VIP PaveX team, which is developing computer vision systems for road condition assessment. The vision side works - we can detect potholes and cracks with over ninety percent accuracy. But we hit a data management bottleneck.
>
> Every time we drive Fort Wayne roads with our camera-equipped vehicle, we're capturing thousands of images. Color images, depth images, GPS coordinates, timestamps. Our Classification Swin model processes these and assigns them to one of eight road condition categories. After multiple collection runs, we had three hundred fifteen megabytes of JSON files with almost three million images referenced.
>
> The challenge wasn't just storage - it was queryability. We need to answer questions like: 'Which segments have the most potholes?' 'How has this road's condition changed over time?' 'Which neighborhoods need the most maintenance?' These require joining data across five levels: segments to drives to cameras to images to classifications.
>
> ### **Our Approach** [Point to Methodology]
>
> We evaluated several options. Traditional relational databases like MySQL would work but aren't optimized for analytics workloads. NoSQL databases like MongoDB are fast but don't support complex joins well. We needed something designed for analytics.
>
> We chose Google Cloud BigQuery for three reasons: **[count on fingers]** One, it's a columnar database, so queries only read the columns they need. Two, it's serverless and auto-scales. Three, it has a SQL interface everyone knows.
>
> ### **ETL Pipeline** [Point to Architecture]
>
> The ETL pipeline is where the real work happens. **[trace the flow on diagram]**
>
> We start with JSON files. Each file contains a nested structure: segments contain drives, drives contain cameras, cameras contain image lists and classifications. Our Python code using Pandas reads these files and flattens them into seven relational tables.
>
> The tricky part is ID generation. The same road segment might appear in multiple files from different collection days. We need consistent IDs. So we use SHA-256 hashing on the segment name to generate a deterministic integer ID. Same segment name always gets the same ID.
>
> We also extract timestamps from image filenames - the filenames are Unix timestamps - and build all the foreign key relationships. Then we validate that we're not missing critical data, and upload to BigQuery in batch.
>
> ### **Schema Design** [Point to tables if shown]
>
> The seven tables are: segments (twenty-six hundred rows), drives (thirty-five hundred rows), cameras (seventy-one hundred rows), images (two point nine million rows), camera-images (five point seven million rows - junction table), categories (eight rows), and image-categories (two million rows).
>
> This normalization means no data duplication and flexible querying. Want all images of potholes from a specific segment? Just join segments → drives → cameras → camera-images → images → image-categories → categories with the appropriate filters.
>
> ### **Performance** [Point to Query Performance chart]
>
> We measured query performance at our current scale of three point eight million images. Simple selects take about one second. Filtered queries and single joins complete in under a second - about point six seconds. Our most complex query - a six-way join across all tables - completes in six and a half seconds.
>
> What's important is that BigQuery's architecture is designed to scale. It achieves this performance through columnar storage and distributed query processing. As our dataset grows with additional data collection, the system will maintain similar performance by automatically parallelizing queries across more machines.
>
> ### **Visualization** [Point to Dashboard - show live if possible]
>
> The Streamlit dashboard has three components: **[point to each if shown]**
>
> One, a Folium heatmap overlaying our data on Fort Wayne shapefiles. We aggregate classifications by segment and color-code them. This gives city planners an immediate visual of problem areas.
>
> Two, a SQL query interface. Users can run custom queries or select from pre-built ones. Results appear as tables they can download.
>
> Three, PowerBI embedded charts showing things like classification distribution, trends over time, camera coverage maps.
>
> ### **Impact & Future Work** [Point to Conclusion]
>
> The immediate impact is for Fort Wayne - they now have a data-driven infrastructure assessment tool. But this architecture scales. We're planning to expand to Indianapolis next.
>
> Future enhancements include real-time streaming - right now it's batch - automated classification integration, and edge computing to process data on the vehicle.
>
> ### **Technical Details**
>
> Some specifics you might be interested in: we're using Python three point thirteen, Pandas for data manipulation, google-cloud-bigquery SDK, Streamlit for the web framework, and Folium for mapping. The BigQuery dataset is called 'autonomous underscore dataset' in the 'vippavexdata' project. Storage costs about twelve cents per month, query costs are under the free tier. Total operational cost is about fifty-five cents per month.
>
> Any specific questions about the implementation?"

**[Wait for questions]**

---

## ❓ COMMON QUESTIONS & ANSWERS

### **Q: "How long did this take to build?"**

> "The project has been ongoing for about a semester. The initial ETL pipeline and BigQuery setup took about three weeks. The dashboard took another two weeks. Most of the time was spent on data cleaning and validation - making sure the relationships were correct across all files."

### **Q: "What programming languages did you use?"**

> "Primarily Python. The ETL pipeline is pure Python using Pandas for data manipulation and the google-cloud-bigquery library for uploads. The dashboard is Streamlit, which is also Python. The SQL queries are obviously SQL. The only non-Python part is PowerBI for some of the embedded visualizations."

### **Q: "Could this work with real-time data?"**

> "Yes, and that's actually our next goal. BigQuery supports streaming inserts, so we could modify our ETL pipeline to process images as they're collected instead of in batches. We'd need to set up a message queue - probably Google Cloud Pub/Sub - to handle the streaming data, but the architecture supports it."

### **Q: "How accurate is the classification model?"**

> "The Classification Swin model - which we didn't develop, we're just using its outputs - achieves over ninety percent accuracy on road condition classification in the literature. But our focus is on the data management side. Even if the model improves or changes, our infrastructure handles the data the same way."

### **Q: "What if a road segment appears in multiple files with different conditions?"**

> "Great question! That's actually really valuable data - it means we can track how a road degrades over time. In our schema, each image has a timestamp, so we can query 'show me all images of segment X ordered by date' and see the progression. That's exactly the kind of temporal analysis city planners want."

### **Q: "Why not use a simpler solution like CSV files?"**

> "We actually considered that. CSVs would work for small datasets, but at two point nine million images, you run into problems. One, CSVs don't enforce relationships, so you could have an image referencing a non-existent segment. Two, querying CSVs is slow - you have to scan the entire file. Three, no concurrency - if multiple people query at once, performance degrades. BigQuery solves all of these."

### **Q: "Is the code open source?"**

> "The code is currently in a private repository for our VIP team, but we're planning to release the ETL pipeline and dashboard code as open source once we clean it up and add documentation. The goal is that other cities could adapt it for their own infrastructure monitoring."

### **Q: "How do you handle data privacy?"**

> "Good question. Fortunately, our images are only of road pavement - no people, no license plates, nothing personally identifiable. The data is also aggregated by segment, not by individual location. But we do use Google Cloud's security features: encryption at rest and in transit, role-based access control, and audit logging."

### **Q: "What was the biggest technical challenge?"**

> "Honestly, ID consistency. When you're processing multiple JSON files that might reference the same segments but use slightly different naming conventions, ensuring that 'segment underscore one two three' in file A is the same as 'segment underscore one two three' in file B required careful hashing. We ended up using SHA-256 on the segment name to generate deterministic IDs, but it took a while to get right."

### **Q: "Could this integrate with existing city systems?"**

> "Absolutely. BigQuery has a REST API, so any system can query it. Cities often use asset management systems like Cityworks or enterprise GIS platforms like ArcGIS. We could export our data to their format or set up API endpoints they can call. That's something we'd work with the city to customize."

### **Q: "How does this compare to commercial solutions?"**

> "Commercial pavement management systems exist - companies like Roadbotics and others. Our advantage is customization and cost. We can adapt our system exactly to research needs or city-specific requirements. And our operational costs are under a dollar per month versus potentially thousands for commercial solutions. The trade-off is we don't have the polish and support of a commercial product."

### **Q: "Will query performance hold up as you add more data?"**

> "Excellent question. The performance numbers I showed are measured at our current scale of three point eight million images. We're still receiving additional data from ongoing collection in Fort Wayne.
>
> The key is that BigQuery is built to scale. Companies use it for petabyte-scale datasets with billions of rows. The architecture uses distributed processing - as data grows, it automatically spreads the work across more machines. We expect similar query times even when we double or triple the dataset.
>
> Plus, we can add optimizations like table partitioning and clustering once we have the full dataset. These help BigQuery skip scanning irrelevant data, keeping queries fast at larger scales."

---

## 🎨 PHYSICAL POSTER TIPS

### **Body Language:**
- **Stand to the SIDE** of your poster, not blocking it
- **Face the audience**, not the poster
- **Point** to specific sections as you talk
- **Make eye contact** when someone approaches
- **Smile** and be enthusiastic!

### **Opening Lines:**
When someone walks up, try one of these:

> "Hi! Are you interested in smart city infrastructure?"

> "Hello! Would you like to hear about our road condition data management project?"

> "Hi there! Can I show you how we're using big data for infrastructure monitoring?"

### **Engagement Tricks:**
- **Ask questions:** "Are you familiar with BigQuery?" or "Do you work with large datasets?"
- **Use comparisons:** "This is like Netflix's recommendation system, but for roads."
- **Tell stories:** "When we first ran the ETL pipeline, it took three hours. Here's how we got it down to ten minutes..."
- **Show enthusiasm:** "The coolest part is..." or "I was really surprised when..."

### **Handling Different Audiences:**

**For Faculty Judges:**
- Use technical terms (normalization, indexing, columnar storage)
- Mention specific technologies (BigQuery, Pandas, Folium)
- Discuss trade-offs (why BigQuery over PostgreSQL)
- Be ready with performance metrics

**For Students:**
- Relate to coursework ("It's like the database class but at real-world scale")
- Mention learning experiences ("I learned a lot about ETL pipelines")
- Encourage questions ("I'm happy to explain any part")

**For Industry Guests:**
- Focus on practical applications (cost savings, decision support)
- Mention scalability (multi-city deployment)
- Discuss integration (API endpoints, data export)

**For General Public:**
- Avoid jargon ("data warehouse" → "organized storage system")
- Use analogies ("It's like organizing millions of photos into albums you can search")
- Focus on impact ("Cities can fix roads before they get really bad")

---

## 📱 DIGITAL BACKUP

**If you have a laptop or tablet:**
- Have your PowerBI dashboard open and ready
- Have Streamlit running locally: `streamlit run home.py`
- Keep a few sample SQL queries ready to demonstrate
- Have photos of example road conditions (good vs bad)

**PowerBI URL (have it bookmarked):**
```
https://app.powerbi.com/view?r=eyJrIjoiMTlkYzY5MmYtZjdlYS00NmQ5LWE1M2UtM2U2ODI5YjlhYzc0IiwidCI6IjQxMzBiZDM5LTdjNTMtNDE5Yy1iMWU1LTg3NThkNmQ2M2YyMSIsImMiOjZ9
```

---

## ⏰ PACING FOR 2-HOUR SESSION

**First 15 minutes:**
- Get settled, tape poster up
- Review your notes
- Practice 30-second pitch once

**During session:**
- Expect 10-15 visitors
- Each interaction: 2-5 minutes
- Stand the entire time (you'll get tired, but it shows engagement)
- Keep water nearby

**Common flow:**
1. Visitor approaches (0:00)
2. You give 30-second pitch (0:30)
3. They ask questions or want more (1:00)
4. You give 2-5 minute explanation (2:00-6:00)
5. Q&A and wrap-up (6:00-8:00)
6. Thank them, wait for next visitor

**Between visitors:**
- Stand ready, make eye contact with people walking by
- Don't sit or look at phone
- If it's slow, read your poster to refresh memory

---

## 🎯 CLOSING LINES

**When wrapping up with someone:**

> "Thank you so much for your interest! If you'd like to learn more, I can share the GitHub repo once it's public. Or feel free to reach out - I'm happy to answer more questions via email."

**If they're a judge:**

> "Thank you for taking the time to review our work! We're really proud of what we've built and excited about where it's heading."

**If they work in the field:**

> "It was great talking to you! If your organization ever needs something similar, we'd love to collaborate or share our learnings."

---

Good luck! Remember: be enthusiastic, make eye contact, and don't worry if you don't know an answer - it's okay to say "That's a great question - I'd need to look into that more!" 🎉
