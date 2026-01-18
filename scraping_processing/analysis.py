from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, split, desc, regexp_extract, length
from pyspark.ml.feature import Tokenizer, StopWordsRemover, CountVectorizer, IDF
from pyspark.ml.clustering import LDA
import pandas as pd
import os

# --- SETUP ---
spark = SparkSession.builder \
    .appName("LightweightAnalysis") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

if not os.path.exists('results'):
    os.makedirs('results')

print("Loading data...")
# CRITICAL FIX 1: Enable multiline option for JSON arrays
try:
    df = spark.read.option("multiline", "true").json("final_data.json")
    print(f"Total Raw Articles: {df.count()}")
    df.printSchema()
except Exception as e:
    print(f"Error loading file: {str(e)}")
    exit()

# --- 1. STATS ANALYSIS ---
print("\n--- Generating Statistics ---")

# Trends (Fixing the regex raw string warning)
try:
    trends = df.filter(col("date_pub").rlike(r"^\d{4}$")) \
               .groupBy("date_pub").count().orderBy("date_pub")
    trends.toPandas().to_csv("results/trends.csv", index=False)
    print("Saved trends.csv")
except Exception as e:
    print(f"Skipping Trends (Column missing?): {e}")

# Authors
if "authors" in df.columns:
    authors = df.withColumn("author", explode(split(col("authors"), ","))) \
                .groupBy("author").count().orderBy(desc("count")).limit(20)
    authors.toPandas().to_csv("results/authors.csv", index=False)
    print("Saved authors.csv")

# Geography
if "affiliations" in df.columns:
    geo = df.withColumn("country", regexp_extract(col("affiliations"), r",\s([A-Za-z]+)$", 1)) \
            .groupBy("country").count().orderBy(desc("count")).limit(20)
    geo.toPandas().to_csv("results/geography.csv", index=False)
    print("Saved geography.csv")

# --- 2. ML ANALYSIS (Topic Modeling) ---
print("\n--- Running Topic Modeling ---")

target_col = "abstract_" if "abstract_" in df.columns else "abstract"

if target_col not in df.columns:
    print("ERROR: No 'abstract' column found. Skipping ML.")
else:
    # Filter valid abstracts
    clean_df = df.filter(col(target_col).isNotNull()) \
                 .filter(col(target_col) != "N/A") \
                 .filter(length(col(target_col)) > 20) \
                 .select(col(target_col).alias("text_content"))

    record_count = clean_df.count()
    print(f"Articles with valid abstracts: {record_count}")

    if record_count > 0:
        # Tokenize
        tokens = Tokenizer(inputCol="text_content", outputCol="words").transform(clean_df)
        remover = StopWordsRemover(inputCol="words", outputCol="filtered")
        cleaned = remover.transform(tokens)

        cv = CountVectorizer(inputCol="filtered", outputCol="rawFeatures", vocabSize=1000, minDF=1.0)
        cv_model = cv.fit(cleaned)
        tf = cv_model.transform(cleaned)
        
        idf = IDF(inputCol="rawFeatures", outputCol="features")
        idf_model = idf.fit(tf) 
        tfidf = idf_model.transform(tf)

        # LDA
        lda = LDA(k=5, maxIter=5)
        model = lda.fit(tfidf)

        # Extract Topics
        vocab = cv_model.vocabulary
        topics_data = []
        try:
            topics = model.describeTopics(5).collect()
            for i, row in enumerate(topics):
                words = [vocab[idx] for idx in row['termIndices']]
                topics_data.append({"Topic": i, "Keywords": ", ".join(words)})
            
            pd.DataFrame(topics_data).to_csv("results/topics.csv", index=False)
            print("Saved topics.csv")
        except Exception as e:
            print(f"Error extracting topics: {e}")

    else:
        print("Skipping ML: No valid text data found (All abstracts are empty or N/A).")

print("\nSUCCESS! Analysis Complete.")
