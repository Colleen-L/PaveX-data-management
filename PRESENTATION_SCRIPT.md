# 🎤 PRESENTATION SCRIPT - Word-by-Word (12 Minutes)

**Research Talk: Data Management for Smart Cities**
**November 19, 2025 | Stewart Center, Room 214**

---

## ⏱️ SLIDE 1: TITLE (30 seconds)

**[Show slide]**

> "Good morning everyone. My name is [YOUR NAME], and today I'm going to talk about our project on Data Management for Smart Cities.
>
> This work was done together with my teammates Colleen Li, Aadit Khurana, and Tran Le Ngoc Vo, under the mentorship of Nikkhil Vijaya Sankar and Professor Mohammad Reza Jahanshahi, as part of the VIP Program here at Purdue."

**[Pause, make eye contact, advance slide]**

---

## ⏱️ SLIDE 2: THE PROBLEM (1 minute 30 seconds)

**[Show slide]**

> "So let me start by explaining the problem we're trying to solve.
>
> **[Point to first bullet]** Computer vision for detecting road conditions like potholes and cracks generates massive amounts of data. In our project alone, we're working with two point nine million images - that's almost three million images - along with over two million classifications.
>
> **[Point to third bullet]** This data covers twenty-six hundred road segments across Fort Wayne, Indiana. And these images aren't just random - they're organized in a complex hierarchy.
>
> **[Gesture showing flow]** We have road segments, which contain driving sessions, which have cameras, which capture images, which get classified into different road condition categories. So we have five levels of relationships to manage.
>
> **[Point to question at bottom]** The question is: how do we efficiently store, query, and visualize all of this data while keeping it useful for machine learning workflows?"

**[Pause 2 seconds, advance slide]**

---

## ⏱️ SLIDE 3: OUR SOLUTION (1 minute 30 seconds)

**[Show slide]**

> "Our solution is to use a cloud-based data warehouse architecture. Let me walk through our technology stack.
>
> **[Point to first item]** First, we chose Google Cloud BigQuery as our storage solution. BigQuery is a columnar data warehouse that's optimized for analytics workloads - which is perfect for our use case of running complex queries across millions of records.
>
> **[Point to second item]** We built a Python ETL pipeline - that's Extract, Transform, Load - to process our three hundred fifteen megabytes of JSON files and convert them into a normalized database schema.
>
> **[Point to third item]** This schema consists of seven relational tables: segments, drives, cameras, images, camera_images, categories, and image_categories. Each table captures one piece of the puzzle.
>
> **[Point to fourth item]** For visualization, we created a Streamlit web application that embeds PowerBI dashboards for analytics.
>
> **[Point to last item]** And finally, we use Folium - that's a Python mapping library - to create interactive heatmaps overlaying our road condition data on Fort Wayne shapefiles."

**[Advance slide]**

---

## ⏱️ SLIDE 4: SYSTEM ARCHITECTURE (1 minute 30 seconds)

**[Show slide with architecture diagram]**

> "This diagram shows how all the pieces fit together.
>
> **[Point to left side]** We start with JSON files - these are the raw outputs from our computer vision classification model called Classification Swin.
>
> **[Point to ETL box]** Our Python ETL pipeline reads these files and performs several critical tasks: it generates consistent IDs across multiple files using hash functions, it extracts timestamps from image filenames, and it builds all the relational mappings.
>
> **[Point to BigQuery]** The processed data goes into Google Cloud BigQuery, where it's stored in our seven tables I mentioned earlier.
>
> **[Point to query layer]** BigQuery provides a SQL interface, so anyone can write queries to explore the data.
>
> **[Point to bottom]** And then we have three visualization layers: our Streamlit dashboard, embedded PowerBI charts, and the Folium heatmap showing road segments color-coded by condition severity.
>
> **[Gesture encompassing whole diagram]** The key thing here is that this architecture is cloud-native, which means it's accessible from anywhere, automatically backed up, and scales as our data grows."

**[Advance slide]**

---

## ⏱️ SLIDE 5: DATA PIPELINE (1 minute 30 seconds)

**[Show slide]**

> "Let me dive deeper into the ETL pipeline, because this is where a lot of the data management challenge happens.
>
> **[Point to left column]** Our input data consists of four JSON files, totaling three hundred fifteen megabytes. These come from the Classification Swin model, which is a transformer-based neural network for image classification.
>
> Each file contains both color and depth images from two cameras, along with classifications into eight different road condition categories. **[Point to category list]** These categories are things like 'Alligator' cracks, 'Longitudinal' cracks, 'Transverse' cracks, manhole covers, and so on.
>
> **[Point to right column]** The processing pipeline has six main steps:
>
> **[Count on fingers]** One: Load the JSON files. Two: Generate consistent IDs - this is important because the same segment might appear in multiple files, so we use SHA-256 hashing to ensure the same segment always gets the same ID. Three: Extract timestamps from the image filenames. Four: Build all the relationships between segments, drives, cameras, images, and classifications. Five: Validate the schema to make sure we're not missing any critical data. And six: Upload everything to BigQuery in batch.
>
> **[Point to result]** The result is seven fully normalized tables where every relationship is properly maintained and queryable."

**[Advance slide]**

---

## ⏱️ SLIDE 6: RESULTS - DATA VOLUMES (1 minute)

**[Show slide with data volume chart]**

> "Now let's look at the results. This chart shows the scale of data we're managing.
>
> **[Point to chart]** You can see that we processed two million eight hundred sixty-two thousand eight hundred thirty-nine images total. That's the blue bar. We generated over two million classifications - that's the orange bar. We're tracking twenty-six hundred road segments and thirty-five hundred driving sessions.
>
> **[Point to key metrics at bottom]** These numbers are important because they demonstrate that our system can handle large-scale real-world data. This isn't a toy example - this is production data from actual road surveys in Fort Wayne.
>
> **[Gesture to whole slide]** And the fact that we can query across all of this data efficiently - which I'll show next - proves that the architecture works at scale."

**[Advance slide]**

---

## ⏱️ SLIDE 7: QUERY PERFORMANCE (1 minute 30 seconds)

**[Show slide with query performance chart]**

> "One of our key evaluation metrics is query performance - how fast can we actually get answers from this data?
>
> **[Point to chart]** This chart shows measured query latency for different types of SQL queries at our current scale of three point eight million images. On the left, we have simple SELECT queries - these take about one second. As we move right, the queries get more complex.
>
> **[Point to middle bars]** Filtered WHERE clauses and single-table JOINs take about point six seconds. When we join multiple tables together - for example, to find all images from a specific segment with certain classifications - these complete in under one second as well.
>
> **[Point to rightmost bars]** The most complex query we tested is a six-way JOIN that connects all seven tables together. This might be something like 'find all segments where longitudinal cracks appear in more than fifty percent of images.' Even this complex query completes in six and a half seconds. This is with three point eight million image records.
>
> **[Gesture to whole chart]** What's important here is that BigQuery's architecture is designed to scale. These measurements demonstrate that we can handle millions of records efficiently, and as the dataset grows, BigQuery's columnar storage and distributed query processing will maintain this performance. It only reads the columns you actually need, and it parallelizes queries across multiple machines automatically."

**[Advance slide]**

---

## ⏱️ SLIDE 8: DASHBOARD (1 minute)

**[Show slide - hopefully with your screenshot]**

> "The whole point of managing this data efficiently is to make it useful, and that's where our dashboard comes in.
>
> **[Point to dashboard screenshot]** This is our Streamlit web application. It has three main features:
>
> **[Point to different parts]** First, there's a Folium heatmap that shows Fort Wayne road segments color-coded by condition. Green means the road is in good shape, orange means moderate issues, and red means significant problems detected. City planners can use this to prioritize maintenance.
>
> Second, we have a SQL query interface. Users can write custom queries or select from pre-built ones to explore the data in any way they need. This is really powerful for researchers who want to ask questions we didn't anticipate.
>
> And third, we embed PowerBI visualizations - things like bar charts of classification distributions, time-series plots of data collection, and so on.
>
> **[Gesture to whole slide]** All of this updates in real-time as new data flows through our ETL pipeline."

**[Advance slide]**

---

## ⏱️ SLIDE 9: IMPACT & APPLICATIONS (1 minute 30 seconds)

**[Show slide]**

> "So what's the impact of this work? I want to highlight both our technical contributions and the real-world applications.
>
> **[Point to left column - Contributions]** On the technical side:
>
> We've demonstrated that cloud-based data warehouses can handle multi-million image datasets efficiently. We've built an ETL pipeline that's reproducible and can be adapted for other cities. We created an interactive dashboard that makes the data accessible to non-technical stakeholders. We provided a SQL interface for researchers. And importantly, we enable easy export of training datasets for machine learning models.
>
> **[Point to right column - Applications]** In terms of real-world applications:
>
> City transportation departments can use this for infrastructure planning - they can see exactly which roads need attention and estimate repair costs. It supports predictive maintenance by identifying trends before roads fail completely. Insurance companies could assess risk for different neighborhoods. ML researchers can use our curated datasets to train better road condition detection models. And the architecture is designed to scale to multiple cities.
>
> **[Gesture broadly]** This is really about making smart cities smarter by giving them the data infrastructure they need to make evidence-based decisions about infrastructure."

**[Advance slide]**

---

## ⏱️ SLIDE 10: NEXT STEPS (1 minute)

**[Show slide]**

> "We're not done yet - there's a lot of exciting future work planned.
>
> **[Point to each item as you read]**
>
> First, we want to implement real-time streaming ETL. Right now, we process data in batches, but we'd like new images to appear in the dashboard as soon as they're collected.
>
> Second, we're working on integrating the classification pipeline directly into our system, so images get automatically classified as they're uploaded instead of in a separate step.
>
> Third, we're planning to expand to other Indiana cities - Indianapolis is our next target. The architecture is already designed for multi-city deployment; we just need to collect the data and shapefiles.
>
> Fourth, we want to add more advanced analytics - things like automatic trend detection, severity scoring algorithms, and prediction of when roads will need maintenance based on historical degradation patterns.
>
> And finally, we're exploring edge computing - can we do some of this processing on the vehicle itself to reduce data transfer costs?"

**[Advance slide]**

---

## ⏱️ SLIDE 11: ACKNOWLEDGMENTS (15 seconds)

**[Show slide]**

> "Before I wrap up, I want to acknowledge the people who made this work possible.
>
> Our mentors, Nikkhil Vijaya Sankar and Professor Mohammad Reza Jahanshahi, provided invaluable guidance throughout the project. The Purdue VIP Program supported us with resources and funding. And of course, the College of Engineering and Google Cloud Platform, which provides the infrastructure we're using."

**[Advance slide]**

---

## ⏱️ SLIDE 12: THANK YOU + Q&A (Remaining ~3 minutes)

**[Show slide]**

> "Thank you very much for your attention. I'm happy to answer any questions."

**[Pause, make eye contact with audience, wait for questions]**

---

## 🎯 HANDLING Q&A (3 minutes)

### **If asked: "Why BigQuery over traditional databases?"**

> "Great question. We chose BigQuery specifically because it's optimized for analytics workloads. Traditional relational databases like MySQL or PostgreSQL are row-oriented, which is great for transactions but slower for analytics. BigQuery is columnar, so when we run a query that only needs a few columns from a table with millions of rows, it only reads those columns. That's a huge performance boost.
>
> Plus, it's serverless - we don't have to manage database servers or worry about scaling. BigQuery automatically distributes the query across as many machines as needed. For an academic project, that's a big advantage."

### **If asked: "What about data privacy or security?"**

> "That's an important concern. The good news is that our road images don't contain personally identifiable information - they're images of pavement, not people or license plates. The Classification Swin model only looks at road conditions.
>
> For security, we use Google Cloud's built-in security features: encryption at rest and in transit, access controls via IAM roles, and audit logging. Only authorized team members can access the BigQuery dataset."

### **If asked: "How much does this cost?"**

> "It's surprisingly affordable. BigQuery storage costs about five cents per gigabyte per month. We're storing about two point five gigabytes, so that's about twelve cents for storage. Query costs are under the free tier because we're not running that many queries in a research setting. Our total monthly cost is around fifty-five cents, mostly from Streamlit dashboard hosting. If this were deployed at city scale, costs would obviously be higher, but still very reasonable."

### **If asked: "Can you show the dashboard live?"**

> "Absolutely! **[If you have laptop]** Let me pull it up quickly. **[Open PowerBI URL or run Streamlit]**
>
> **[If you don't have laptop ready]** Unfortunately I don't have it loaded right now, but I can send you the link after the presentation if you'd like to explore it yourself."

### **If asked: "How long does the ETL pipeline take?"**

> "For our three hundred fifteen megabytes of JSON data, the entire ETL process - reading files, processing, validating, and uploading to BigQuery - takes about eight to ten minutes on a standard laptop. That breaks down to roughly two to three minutes per hundred megabytes. If we parallelize the processing, we could speed that up significantly."

### **If asked: "What's the accuracy of the classification model?"**

> "That's a great question about the Classification Swin model. We're not the ones who developed that model - we're consuming its outputs. From the literature, Swin Transformer-based models typically achieve over ninety percent accuracy on road condition classification tasks. But our project focuses on the data management side - how to efficiently store and query the results, regardless of which classification model is used."

### **If asked: "Could this work for other infrastructure monitoring?"**

> "Absolutely! The architecture is quite general. You could use the same approach for monitoring bridges, sidewalks, building facades, or really any infrastructure where you're collecting images with associated classifications and geospatial data. You'd just need to adapt the ETL pipeline to your specific data format and adjust the dashboard visualizations. The core BigQuery structure would work the same way."

### **If asked: "Will performance scale when you add more data?"**

> "Great question. The query performance metrics I showed are measured at our current scale of three point eight million images. We're still receiving additional data from ongoing collection efforts in Fort Wayne.
>
> The good news is that BigQuery is designed to handle petabyte-scale datasets. Companies use it for billions of rows. The architecture uses distributed processing and columnar storage, so as data grows, BigQuery automatically scales the query execution across more machines. We expect query times to remain in the same general range even as we double or triple the dataset size.
>
> Additionally, we can optimize further by adding partitioning and clustering to our tables once we have the complete dataset. These features help BigQuery prune the data it needs to scan, keeping queries fast even at much larger scales."

### **If asked: "Why is the complex query so much slower?"**

> "That's a perceptive observation. The six-way JOIN is slower - about six and a half seconds versus under one second for simpler queries - because it has to connect all seven tables together and match millions of records across multiple relationships.
>
> Think about what it's doing: starting from image classifications, joining to images, to camera-image mappings, to cameras, to drives, to segments, and to categories. That's traversing the entire data hierarchy. Even so, six and a half seconds to analyze millions of records across seven tables is quite good for an analytics query.
>
> For context, running the same type of query on a traditional row-based database would likely take much longer - potentially minutes instead of seconds."

---

## 📝 TIMING NOTES

**Total time budget: 15 minutes**

- Slides 1-3: ~3.5 minutes (Intro + Problem + Solution)
- Slides 4-6: ~4 minutes (Architecture + Pipeline + Results)
- Slides 7-9: ~4 minutes (Performance + Dashboard + Impact)
- Slides 10-11: ~1 minute (Next Steps + Acknowledgments)
- Slide 12 + Q&A: ~2.5 minutes

**Tips:**
- Speak at a moderate pace - don't rush!
- Pause between slides for 1-2 seconds
- Make eye contact, don't just read slides
- Use hand gestures to point at charts
- Smile and show enthusiasm
- Have water nearby

**If running over time:**
- Shorten Slide 5 (Data Pipeline) - skip detailed steps
- Shorten Slide 10 (Next Steps) - mention only 2-3 items
- Skip one of the Q&A prep answers if not asked

**If running under time:**
- Add more detail on Slide 7 (Query Performance)
- Spend more time on Slide 8 (Dashboard demo)
- Add personal anecdotes about challenges you faced

Good luck! You got this! 🎉
